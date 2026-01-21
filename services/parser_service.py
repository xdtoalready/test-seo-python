import httpx
import trafilatura
import json
from pathlib import Path
from typing import Optional, Dict
from loguru import logger
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type
)

from config import settings
from config.constants import (
    HTTP_REQUEST_TIMEOUT,
    DEFAULT_USER_AGENT,
    MIN_PAGE_CONTENT_LENGTH,
    MAX_PAGE_CONTENT_LENGTH
)


class ParserError(Exception):
    """Ошибка при парсинге страницы"""
    pass


class ParserService:
    """Сервис для парсинга веб-страниц"""

    def __init__(self):
        self.timeout = HTTP_REQUEST_TIMEOUT
        self.user_agent = DEFAULT_USER_AGENT
        self.min_length = settings.min_content_length
        self.max_length = settings.max_content_length
        self.demo_mode = settings.demo_mode

        if self.demo_mode:
            logger.info("🎭 DEMO MODE: Using mock parser data")

    def _load_mock_parser_data(self) -> list[Dict[str, any]]:
        """
        Загрузить mock данные парсера для demo режима

        Returns:
            Список с контентом страниц
        """
        mock_file = Path(__file__).parent.parent / "mock_data" / "parser_example.json"

        try:
            with open(mock_file, "r", encoding="utf-8") as f:
                contents = json.load(f)
                logger.info(f"🎭 Loaded {len(contents)} mock contents from {mock_file.name}")
                return contents
        except Exception as e:
            logger.error(f"❌ Failed to load mock parser data: {e}")
            # Fallback mock данные
            return [
                {
                    "url": "https://example1.com",
                    "text": "Пример текста о выкупе автомобилей. Необходимые документы: паспорт, ПТС, СТС."
                },
                {
                    "url": "https://example2.com",
                    "text": "Быстрый выкуп авто. Оценка по фото в WhatsApp. Моментальная оплата."
                }
            ]
    
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    async def download_html(self, url: str) -> str:
        """
        Скачать HTML страницы
        
        Args:
            url: URL страницы
            
        Returns:
            HTML содержимое
            
        Raises:
            ParserError: Если не удалось скачать
        """
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                
                logger.debug(f"📥 Downloading: {url}")
                
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Accept-Encoding": "gzip, deflate",
                        "Connection": "keep-alive",
                    }
                )
                
                response.raise_for_status()
                
                # Проверка Content-Type
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type:
                    raise ParserError(f"Not HTML content: {content_type}")
                
                html = response.text
                logger.debug(f"✅ Downloaded {len(html)} bytes from {url}")
                
                return html
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error {e.response.status_code} for {url}")
            raise ParserError(f"HTTP {e.response.status_code}")
        
        except httpx.TimeoutException:
            logger.error(f"⏱️ Timeout for {url}")
            raise ParserError("Request timeout")
        
        except Exception as e:
            logger.error(f"❌ Error downloading {url}: {e}")
            raise ParserError(f"Download failed: {str(e)}")
    
    def extract_text_from_html(self, html: str, url: str = "") -> Optional[str]:
        """
        Извлечь чистый текст из HTML с помощью trafilatura
        
        Args:
            html: HTML содержимое
            url: URL источника (для логов)
            
        Returns:
            Чистый текст или None
        """
        
        try:
            logger.debug(f"🔍 Extracting text with trafilatura...")
            
            # Trafilatura - лучший инструмент для извлечения основного контента
            text = trafilatura.extract(
                html,
                include_comments=False,  # Без комментариев
                include_tables=True,     # Включить таблицы
                no_fallback=False,       # Использовать fallback если основной метод не сработал
                favor_precision=True,    # Точность важнее полноты
                favor_recall=False,
                with_metadata=False,     # Без метаданных
            )
            
            if not text:
                logger.warning(f"⚠️ Trafilatura returned empty text for {url}")
                return None
            
            # Очистка и нормализация
            text = self._clean_text(text)
            
            logger.debug(f"✅ Extracted {len(text)} chars")
            return text
            
        except Exception as e:
            logger.error(f"❌ Error extracting text: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """
        Очистить и нормализовать текст
        
        Args:
            text: Сырой текст
            
        Returns:
            Очищенный текст
        """
        
        # Удалить лишние пробелы и переносы строк
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        text = '\n'.join(lines)
        
        # Удалить повторяющиеся пробелы
        import re
        text = re.sub(r' +', ' ', text)
        
        # Удалить повторяющиеся переносы строк (больше 2 подряд)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    async def extract_content(self, url: str) -> Optional[Dict[str, any]]:
        """
        Полный цикл: скачать HTML → извлечь текст → проверить длину
        
        Args:
            url: URL страницы
            
        Returns:
            Dict с контентом или None
            {
                "url": str,
                "text": str,
                "length": int,
                "truncated": bool
            }
        """
        
        logger.info(f"📄 Processing: {url}")
        
        try:
            # 1. Скачать HTML
            html = await self.download_html(url)
            
            if not html:
                logger.warning(f"⚠️ Empty HTML from {url}")
                return None
            
            # 2. Извлечь текст
            text = self.extract_text_from_html(html, url)
            
            if not text:
                logger.warning(f"⚠️ No text extracted from {url}")
                return None
            
            # 3. Проверить минимальную длину
            if len(text) < self.min_length:
                logger.warning(
                    f"⚠️ Content too short from {url}: {len(text)} < {self.min_length} chars"
                )
                return None
            
            # 4. Обрезать если слишком длинный (экономия токенов)
            truncated = False
            if len(text) > self.max_length:
                logger.info(
                    f"✂️ Truncating content from {url}: {len(text)} -> {self.max_length}"
                )
                text = text[:self.max_length]
                truncated = True
            
            result = {
                "url": url,
                "text": text,
                "length": len(text),
                "truncated": truncated
            }
            
            logger.info(
                f"✅ Extracted {len(text)} chars from {url} "
                f"(truncated={truncated})"
            )
            
            return result
            
        except ParserError as e:
            logger.error(f"❌ Parser error for {url}: {e}")
            return None
        
        except Exception as e:
            logger.error(f"❌ Unexpected error for {url}: {e}", exc_info=True)
            return None
    
    async def extract_multiple(self, urls: list[str]) -> list[Dict[str, any]]:
        """
        Извлечь контент из нескольких URL параллельно

        Args:
            urls: Список URL

        Returns:
            Список словарей с контентом
        """

        # DEMO MODE: возвращаем mock данные
        if self.demo_mode:
            logger.info(f"🎭 DEMO MODE: Returning mock parser data for {len(urls)} URLs")
            mock_data = self._load_mock_parser_data()
            # Подменяем URL в mock данных на запрошенные
            for i, item in enumerate(mock_data):
                if i < len(urls):
                    item["url"] = urls[i]
            return mock_data[:len(urls)]

        # PRODUCTION MODE: реальный парсинг
        logger.info(f"📦 Processing {len(urls)} URLs...")

        import asyncio

        # Запускаем все задачи параллельно
        tasks = [self.extract_content(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Фильтруем успешные результаты
        contents = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Task {i} failed: {result}")
                continue

            if result is not None:
                contents.append(result)

        logger.info(f"✅ Successfully processed {len(contents)}/{len(urls)} URLs")

        return contents


# Глобальный экземпляр
parser_service = ParserService()