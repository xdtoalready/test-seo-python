import json
import re
from typing import List, Dict, Optional
from loguru import logger
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type
)

from openai import AsyncOpenAI, OpenAIError
from config import settings
from config.constants import (
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    OPENROUTER_TIMEOUT
)


class LLMError(Exception):
    """Ошибка при работе с LLM"""
    pass


class LLMService:
    """Сервис для работы с DeepSeek V3.2 через OpenRouter"""

    # Entity types for structured extraction
    ENTITY_TYPES = ["SERVICE", "CONDITION", "REQUIREMENT", "PROCESS", "DOCUMENT", "CHANNEL", "BENEFIT", "GEO"]

    # Allowed relations (must match relation_canonicalizer.py)
    ALLOWED_RELATIONS = [
        "offers", "has_condition", "has_requirement", "requires_document",
        "done_via", "available_in", "gives_benefit", "has_step"
    ]

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=OPENROUTER_TIMEOUT,
            default_headers={
                "HTTP-Referer": "https://seo-analyzer.local",
                "X-Title": "SEO Entity Analyzer",
            }
        )

        self.model = settings.openrouter_model

        if not settings.openrouter_api_key:
            logger.warning("⚠️ OPENROUTER_API_KEY not configured!")

    def _get_system_prompt(self) -> str:
        """
        Get system prompt for entity extraction.
        Separate system message improves format adherence.
        """
        return """Ты — движок извлечения знаний из SEO-страниц. Из текста нужно извлечь сквозные бизнес-сущности и связи между ними так, чтобы на разных сайтах по одной теме получались одинаковые каноничные сущности.

Верни ТОЛЬКО валидный JSON-массив. Никаких пояснений, Markdown, текста "вот результат". Если извлечь нечего — верни [].

ТИПЫ СУЩНОСТЕЙ (старайся покрыть максимум классов):
- SERVICE — услуга/продукт/предложение (главная тема и её варианты)
- CONDITION — условия (срок, сумма, цена, тариф, процент, гарантия, сроки выполнения)
- REQUIREMENT — требования/критерии (возраст, документы, ограничения, кому подходит/не подходит)
- PROCESS — шаги/процедуры (оформление, заявка, доставка, диагностика, оплата, получение результата)
- DOCUMENT — документы/бумаги/справки/договоры
- CHANNEL — каналы/способы (онлайн, офис, курьер, WhatsApp/телефон как канал, карта/наличные как способ)
- BENEFIT — выгоды (без переплат, быстро, официально, акция) — только если это не чистый маркетинговый мусор
- GEO — гео/регион/город (если реально в тексте)

СВЯЗИ (используй ТОЛЬКО из списка):
- offers — предлагает/предоставляет услугу
- has_condition — имеет условие (срок, цена, процент)
- has_requirement — имеет требование (возраст, документ, ограничение)
- requires_document — требует документ
- done_via — осуществляется через/выполняется посредством
- available_in — доступно в (канал, место, способ)
- gives_benefit — даёт выгоду/преимущество
- has_step — включает шаг/этап

НОРМАЛИЗАЦИЯ (обязательно):
Для каждой сущности укажи:
- text — как в тексте (коротко, 2-5 слов)
- canonical — нормализованная форма, одинаковая для синонимов ("авто/машина/автомобиль" → "автомобиль", "паспорт/удостоверение личности" → "паспорт")
- type — тип из списка выше

Правило: canonical должен быть 2-5 слов, без брендов и "воды". Если уже использовал canonical — используй В ТОЧНОСТИ ту же строку снова.

ФОРМАТ РЕЗУЛЬТАТА:
[
  {
    "entity_1": {"text": "Займ без процентов", "canonical": "беспроцентный займ", "type": "SERVICE"},
    "relation": "has_condition",
    "entity_2": {"text": "до 30 дней", "canonical": "срок до 30 дней", "type": "CONDITION"},
    "context": "Первый займ без процентов на срок до 30 дней"
  }
]

ЖЁСТКИЕ ПРАВИЛА:
- Максимум 25 связок. Минимум 12, если текст не пустой.
- Игнорируй меню/футер/копирайт/политику/куки.
- Повторяющиеся понятия ВСЕГДА своди к одному canonical.
- Не выдумывай факты, которых нет в тексте.
- ТОЛЬКО JSON-массив, никакого текста до или после."""

    def _build_user_prompt(self, text: str) -> str:
        """
        Build user prompt with text to analyze.

        Args:
            text: Text to analyze

        Returns:
            User prompt
        """
        return f"Текст для анализа:\n\n{text}"

    def _build_prompt(self, text: str) -> str:
        """
        Legacy method - builds combined prompt.
        Kept for backward compatibility.

        Args:
            text: Text to analyze

        Returns:
            Combined prompt
        """
        return f"{self._get_system_prompt()}\n\n{self._build_user_prompt(text)}"
    
    def _extract_json_from_response(self, text: str) -> List[Dict]:
        """
        Extract JSON from LLM response (handles markdown, extra text).

        Args:
            text: LLM response

        Returns:
            List of entities

        Raises:
            LLMError: If JSON parsing fails
        """

        try:
            # Remove markdown code blocks if present
            text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'```\s*', '', text)

            # Remove any comments before JSON
            text = re.sub(r'^[^[\{]*', '', text)

            # Find first [ and last ]
            start = text.find('[')
            end = text.rfind(']')

            if start == -1 or end == -1:
                raise ValueError("No JSON array found in response")

            json_text = text[start:end + 1]

            # Fix common JSON errors - trailing commas
            json_text = re.sub(r',(\s*[\]}])', r'\1', json_text)

            # Parse JSON
            entities = json.loads(json_text)

            if not isinstance(entities, list):
                raise ValueError("Response is not a JSON array")

            logger.debug(f"✅ Parsed {len(entities)} entities from response")
            return entities

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            logger.debug(f"Response text (first 500 chars): {text[:500]}")

            # Try to recover JSON more aggressively
            try:
                start = text.find('[')
                if start != -1:
                    json_text = text[start:]
                    json_text = re.sub(r'\}\s*[^,\]]*$', '}]', json_text)
                    entities = json.loads(json_text)
                    logger.warning(f"⚠️ Recovered {len(entities)} entities from malformed JSON")
                    return entities
            except:
                pass

            raise LLMError(f"Invalid JSON in response: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Error extracting JSON: {e}")
            raise LLMError(f"Failed to extract JSON: {str(e)}")

    def _normalize_entity(self, entity: Dict) -> Dict:
        """
        Normalize entity from new format to flat format for aggregator.

        New format:
        {
            "entity_1": {"text": "...", "canonical": "...", "type": "..."},
            "relation": "...",
            "entity_2": {"text": "...", "canonical": "...", "type": "..."},
            "context": "..."
        }

        Flat format (for aggregator):
        {
            "entity_1": "canonical string",
            "entity_1_text": "original text",
            "entity_1_type": "type",
            "relation": "relation",
            "entity_2": "canonical string",
            "entity_2_text": "original text",
            "entity_2_type": "type",
            "context": "..."
        }

        Also handles legacy flat format for backward compatibility.

        Args:
            entity: Entity in new or legacy format

        Returns:
            Normalized entity in flat format
        """
        result = {}

        # Handle entity_1
        e1 = entity.get('entity_1', '')
        if isinstance(e1, dict):
            # New format with canonical
            result['entity_1'] = e1.get('canonical') or e1.get('text', '')
            result['entity_1_text'] = e1.get('text', '')
            result['entity_1_type'] = e1.get('type', 'UNKNOWN')
        else:
            # Legacy flat format
            result['entity_1'] = str(e1) if e1 else ''
            result['entity_1_text'] = str(e1) if e1 else ''
            result['entity_1_type'] = 'UNKNOWN'

        # Handle entity_2
        e2 = entity.get('entity_2', '')
        if isinstance(e2, dict):
            result['entity_2'] = e2.get('canonical') or e2.get('text', '')
            result['entity_2_text'] = e2.get('text', '')
            result['entity_2_type'] = e2.get('type', 'UNKNOWN')
        else:
            result['entity_2'] = str(e2) if e2 else ''
            result['entity_2_text'] = str(e2) if e2 else ''
            result['entity_2_type'] = 'UNKNOWN'

        # Relation (always string)
        result['relation'] = entity.get('relation', '')

        # Context (optional)
        result['context'] = entity.get('context', '')

        return result
    
    def _validate_entity(self, entity: Dict) -> bool:
        """
        Validate entity structure (supports new and legacy formats).

        Args:
            entity: Entity to validate

        Returns:
            True if valid
        """
        required_fields = ["entity_1", "relation", "entity_2"]

        # Check required fields exist
        if not all(field in entity for field in required_fields):
            logger.warning(f"⚠️ Entity missing required fields: {entity}")
            return False

        # Validate entity_1
        e1 = entity.get('entity_1')
        if isinstance(e1, dict):
            # New format - need text or canonical
            if not (e1.get('text') or e1.get('canonical')):
                logger.warning(f"⚠️ Entity_1 missing text/canonical: {entity}")
                return False
        elif not str(e1).strip():
            logger.warning(f"⚠️ Entity_1 is empty: {entity}")
            return False

        # Validate entity_2
        e2 = entity.get('entity_2')
        if isinstance(e2, dict):
            if not (e2.get('text') or e2.get('canonical')):
                logger.warning(f"⚠️ Entity_2 missing text/canonical: {entity}")
                return False
        elif not str(e2).strip():
            logger.warning(f"⚠️ Entity_2 is empty: {entity}")
            return False

        # Validate relation
        rel = entity.get('relation', '')
        if not str(rel).strip():
            logger.warning(f"⚠️ Relation is empty: {entity}")
            return False

        return True
    
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(OpenAIError)
    )
    async def extract_entities(
        self,
        text: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ) -> List[Dict]:
        """
        Extract entities from text using DeepSeek V3.2.

        Uses separate system and user messages for better format adherence.

        Args:
            text: Text to analyze
            temperature: Model temperature (0.0-1.0), lower = more consistent
            max_tokens: Maximum tokens in response

        Returns:
            List of entities in normalized flat format:
            [
                {
                    "entity_1": str (canonical),
                    "entity_1_text": str (original),
                    "entity_1_type": str,
                    "relation": str,
                    "entity_2": str (canonical),
                    "entity_2_text": str (original),
                    "entity_2_type": str,
                    "context": str (optional)
                },
                ...
            ]

        Raises:
            LLMError: If request fails
        """

        logger.info(f"🤖 Analyzing text with DeepSeek V3.2 ({len(text)} chars)...")

        try:
            # Use separate system and user messages for better adherence
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_user_prompt(text)

            # Request to OpenRouter with system + user messages
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response text
            response_text = response.choices[0].message.content

            logger.debug(f"📥 LLM response: {len(response_text)} chars")

            # Parse JSON
            raw_entities = self._extract_json_from_response(response_text)

            # Validate and normalize entities
            valid_entities = []
            for entity in raw_entities:
                if self._validate_entity(entity):
                    # Normalize to flat format for aggregator
                    normalized = self._normalize_entity(entity)
                    valid_entities.append(normalized)

            if len(valid_entities) < len(raw_entities):
                logger.warning(
                    f"⚠️ Filtered out {len(raw_entities) - len(valid_entities)} invalid entities"
                )

            logger.info(f"✅ Extracted {len(valid_entities)} valid entities")

            return valid_entities

        except OpenAIError as e:
            logger.error(f"❌ OpenRouter API error: {e}")
            raise LLMError(f"API request failed: {str(e)}")

        except LLMError:
            raise

        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            raise LLMError(f"Unexpected error: {str(e)}")
    
    async def analyze_url(
        self,
        url: str,
        text: str
    ) -> Dict[str, any]:
        """
        Полный анализ контента одного URL
        
        Args:
            url: URL источника
            text: Текст для анализа
            
        Returns:
            {
                "url": str,
                "entities": List[Dict],
                "entity_count": int
            }
        """
        
        logger.info(f"📊 Analyzing content from {url}")
        
        try:
            entities = await self.extract_entities(text)
            
            result = {
                "url": url,
                "entities": entities,
                "entity_count": len(entities)
            }
            
            logger.info(f"✅ Found {len(entities)} entities in {url}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze {url}: {e}")
            raise


# Глобальный экземпляр
llm_service = LLMService()