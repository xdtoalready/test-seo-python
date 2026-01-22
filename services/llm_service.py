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
    
    def _build_prompt(self, text: str) -> str:
        """
        Построить промпт для извлечения сущностей
        
        Args:
            text: Текст для анализа
            
        Returns:
            Промпт для ИИ
        """
        
        prompt = f"""Ты эксперт по анализу SEO контента. Твоя задача - извлечь семантические сущности (entities) и связи между ними из предоставленного текста.

ВАЖНО:
1. Ищи не просто слова, а смыслы. Например, "автомобиль", "машина", "авто" - это одна сущность.
2. Сущность - это конкретный объект или понятие, связанное с бизнес-процессом.
3. Связь - это глагол или отношение между двумя сущностями.

ФОРМАТ ОТВЕТА (ОБЯЗАТЕЛЬНО JSON, БЕЗ ДОПОЛНИТЕЛЬНОГО ТЕКСТА):
[
  {{
    "entity_1": "Выкуп битых автомобилей",
    "relation": "требует",
    "entity_2": "Паспорт транспортного средства",
    "context": "Для сделки требуется паспорт ТС или ПТС"
  }},
  {{
    "entity_1": "Оценка автомобиля",
    "relation": "может_быть",
    "entity_2": "По фото в WhatsApp",
    "context": "Клиент может отправить фото машины в WhatsApp для оценки"
  }}
]

ВАЖНЫЕ ПРАВИЛА:
- Минимум сущности: 2-3 слова (не "авто", а "Выкуп автомобилей").
- Максимум сущности: одна фраза из 4-6 слов (не весь предложение).
- Связи: используй простые глаголы ("требует", "предоставляет", "включает", "может_быть", "осуществляется").
- Игнорируй сущности из меню, копирайта, юридических оговорок (если только они не про бизнес-процесс).
- Если один концепт повторяется в разном контексте (например, "Документы" и "Необходимые документы"), объедини их в одну сущность.
- Выдай массив JSON. НИЧЕГО БОЛЬШЕ. Не пиши "Вот результат:", не добавляй комментарии, не используй markdown code blocks.
- Найди минимум 5-10 связок, максимум 30.

ТЕКСТ ДЛЯ АНАЛИЗА:
{text}

JSON:"""
        
        return prompt
    
    def _extract_json_from_response(self, text: str) -> List[Dict]:
        """
        Извлечь JSON из ответа ИИ (на случай если есть markdown или текст)
        
        Args:
            text: Ответ от ИИ
            
        Returns:
            Список сущностей
            
        Raises:
            LLMError: Если не удалось распарсить JSON
        """
        
        try:
            # Убрать markdown code blocks если есть
            text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'```\s*', '', text)

            # Убрать возможные комментарии в начале
            text = re.sub(r'^[^[\{]*', '', text)

            # Найти первый [ и последний ]
            start = text.find('[')
            end = text.rfind(']')

            if start == -1 or end == -1:
                raise ValueError("No JSON array found in response")

            json_text = text[start:end + 1]

            # Попытка исправить распространенные ошибки JSON
            # Убрать trailing запятые перед ] и }
            json_text = re.sub(r',(\s*[\]}])', r'\1', json_text)

            # Парсинг JSON
            entities = json.loads(json_text)

            if not isinstance(entities, list):
                raise ValueError("Response is not a JSON array")

            logger.debug(f"✅ Parsed {len(entities)} entities from response")
            return entities

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            logger.debug(f"Response text (first 500 chars): {text[:500]}")

            # Попытка восстановить JSON более агрессивно
            try:
                # Найти последний валидный объект перед ошибкой
                start = text.find('[')
                if start != -1:
                    # Попробуем найти валидные объекты построчно
                    json_text = text[start:]
                    # Убрать все после последней закрывающей скобки объекта
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
    
    def _validate_entity(self, entity: Dict) -> bool:
        """
        Проверить что сущность имеет правильную структуру
        
        Args:
            entity: Сущность для проверки
            
        Returns:
            True если валидна
        """
        
        required_fields = ["entity_1", "relation", "entity_2"]
        
        # Проверка наличия обязательных полей
        if not all(field in entity for field in required_fields):
            logger.warning(f"⚠️ Entity missing required fields: {entity}")
            return False
        
        # Проверка что поля не пустые
        if not all(entity.get(field, "").strip() for field in required_fields):
            logger.warning(f"⚠️ Entity has empty fields: {entity}")
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
        Извлечь сущности из текста с помощью DeepSeek V3.2
        
        Args:
            text: Текст для анализа
            temperature: Температура модели (0.0-1.0)
            max_tokens: Максимум токенов в ответе
            
        Returns:
            Список сущностей в формате:
            [
                {
                    "entity_1": str,
                    "relation": str,
                    "entity_2": str,
                    "context": str (optional)
                },
                ...
            ]
            
        Raises:
            LLMError: Если запрос не удался
        """
        
        logger.info(f"🤖 Analyzing text with DeepSeek V3.2 ({len(text)} chars)...")
        
        try:
            # Построить промпт
            prompt = self._build_prompt(text)
            
            # Запрос к OpenRouter
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Извлечь текст ответа
            response_text = response.choices[0].message.content
            
            logger.debug(f"📥 LLM response: {len(response_text)} chars")
            
            # Парсинг JSON
            entities = self._extract_json_from_response(response_text)
            
            # Валидация сущностей
            valid_entities = [e for e in entities if self._validate_entity(e)]
            
            if len(valid_entities) < len(entities):
                logger.warning(
                    f"⚠️ Filtered out {len(entities) - len(valid_entities)} invalid entities"
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