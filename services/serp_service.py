import httpx
from typing import List, Dict, Any, Optional
from loguru import logger
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type
)

from config import settings
from config.constants import (
    YANDEX_REGIONS,
    HTTP_REQUEST_TIMEOUT,
    DEFAULT_USER_AGENT
)


class SerpAPIError(Exception):
    """Ошибка при работе с SerpAPI"""
    pass


class SerpService:
    """Сервис для работы с SerpAPI"""
    
    def __init__(self):
        self.api_key = settings.serpapi_key
        self.base_url = "https://serpapi.com/search"
        
        if not self.api_key:
            logger.warning("⚠️ SERPAPI_KEY not configured!")
    
    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=30),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, SerpAPIError)),
        before_sleep=lambda retry_state: logger.warning(
            f"⏳ SerpAPI retry attempt {retry_state.attempt_number}/5 after {retry_state.outcome.exception()}"
        )
    )
    async def _make_request(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Выполнить запрос к SerpAPI с retry логикой

        Args:
            params: Параметры запроса

        Returns:
            JSON ответ от SerpAPI

        Raises:
            SerpAPIError: Если запрос не удался
        """

        try:
            async with httpx.AsyncClient(timeout=HTTP_REQUEST_TIMEOUT) as client:
                logger.info(f"🔍 SerpAPI request: query='{params.get('text')}', engine={params.get('engine')}, page={params.get('p', 0)}")

                response = await client.get(
                    self.base_url,
                    params=params
                )

                response.raise_for_status()
                data = response.json()

                # Проверка на ошибки от SerpAPI
                if "error" in data:
                    error_msg = data['error']
                    logger.error(f"❌ SerpAPI returned error: {error_msg}")
                    raise SerpAPIError(f"SerpAPI error: {error_msg}")

                logger.info(f"✅ SerpAPI request successful: {len(data.get('organic_results', []))} results")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error from SerpAPI: {e.response.status_code} - {e.response.text[:200]}")
            raise SerpAPIError(f"HTTP {e.response.status_code}: {e.response.text}")

        except httpx.TimeoutException as e:
            logger.error(f"⏱️ SerpAPI request timeout after {HTTP_REQUEST_TIMEOUT}s")
            raise SerpAPIError(f"Request timeout after {HTTP_REQUEST_TIMEOUT}s")

        except SerpAPIError:
            raise

        except Exception as e:
            logger.error(f"❌ Unexpected error in SerpAPI request: {e}", exc_info=True)
            raise SerpAPIError(f"Unexpected error: {str(e)}")
    
    async def get_yandex_results(
        self,
        keyword: str,
        region_id: Optional[int] = None,
        depth: int = 10
    ) -> List[str]:
        """
        Получить результаты поиска из Яндекса
        
        Args:
            keyword: Поисковый запрос
            region_id: ID региона из yandex_region.json (lr параметр)
            depth: Количество результатов (макс 100)
            
        Returns:
            Список URL из результатов поиска
        """
        
        logger.info(f"🔍 Fetching Yandex SERP: '{keyword}' (region_id={region_id or 'default'}, depth={depth})")

        urls = []
        blacklisted_count = 0
        pages_needed = (depth // 10) + (1 if depth % 10 else 0)

        for page in range(pages_needed):
            try:
                # Параметры для Яндекса
                params = {
                    "text": keyword,  # для Яндекса используется "text"
                    "engine": "yandex",
                    "api_key": self.api_key,
                    "lang": "ru",
                    "p": page,
                }
                
                # Добавить региональный код если указан
                if region_id:
                    params["lr"] = region_id
                    logger.debug(f"📍 Using Yandex region ID: {region_id}")
                
                # Выполнить запрос
                data = await self._make_request(params)
                
                # Извлечь URL из результатов
                organic_results = data.get("organic_results", [])
                
                if not organic_results:
                    logger.warning(f"⚠️ No organic results on page {page}")
                    break
                
                # Фильтровать и собирать URL
                for result in organic_results:
                    url = result.get("link")

                    if not url:
                        continue

                    # Проверка на blacklist
                    if self._is_blacklisted(url):
                        blacklisted_count += 1
                        logger.debug(f"🚫 Skipped blacklisted URL: {url}")
                        continue

                    urls.append(url)
                    logger.debug(f"✅ Added URL #{len(urls)}: {url}")

                    if len(urls) >= depth:
                        if blacklisted_count > 0:
                            logger.info(f"🚫 Filtered {blacklisted_count} blacklisted URLs")
                        logger.info(f"✅ Collected {len(urls)} URLs (target: {depth})")
                        return urls

                logger.info(f"📄 Page {page}: collected {len(organic_results)} results")

            except SerpAPIError as e:
                logger.error(f"❌ Error on page {page}: {str(e)}")
                if page == 0:
                    raise
                break

        if blacklisted_count > 0:
            logger.info(f"🚫 Total blacklisted URLs filtered: {blacklisted_count}")
        logger.info(f"✅ Total URLs collected: {len(urls)} (target: {depth})")
        return urls

    async def get_google_results(
        self,
        keyword: str,
        location: str = "Russia",
        depth: int = 10
    ) -> List[str]:
        """
        Получить результаты поиска из Google
        
        Args:
            keyword: Поисковый запрос
            location: Название региона (например, "Москва") или страны ("Russia")
            depth: Количество результатов (макс 100)
            
        Returns:
            Список URL из результатов поиска
        """
        
        logger.info(f"🔍 Fetching Google SERP: '{keyword}' (location={location}, depth={depth})")

        urls = []
        blacklisted_count = 0
        pages_needed = (depth // 10) + (1 if depth % 10 else 0)

        for page in range(pages_needed):
            try:
                # Параметры для Google
                params = {
                    "q": keyword,
                    "engine": "google",
                    "api_key": self.api_key,
                    "hl": "ru",
                    "google_domain": "google.ru",  # Важно для кириллицы
                    "location": location,  # Название региона или страны
                    "start": page * 10,
                }
                
                logger.debug(f"📍 Google location: {location}")
                
                # Выполнить запрос
                try:
                    data = await self._make_request(params)
                except SerpAPIError as e:
                    # Фолбэк: если ошибка с location, пробуем "Russia"
                    if "location" in str(e).lower() and location != "Russia":
                        logger.warning(f"⚠️ Location '{location}' not supported, fallback to 'Russia'")
                        params["location"] = "Russia"
                        data = await self._make_request(params)
                    else:
                        raise
                
                # Извлечь URL из результатов
                organic_results = data.get("organic_results", [])
                
                if not organic_results:
                    logger.warning(f"⚠️ No organic results on page {page}")
                    break
                
                # Фильтровать и собирать URL
                for result in organic_results:
                    url = result.get("link")

                    if not url:
                        continue

                    if self._is_blacklisted(url):
                        blacklisted_count += 1
                        logger.debug(f"🚫 Skipped blacklisted URL: {url}")
                        continue

                    urls.append(url)
                    logger.debug(f"✅ Added URL #{len(urls)}: {url}")

                    if len(urls) >= depth:
                        if blacklisted_count > 0:
                            logger.info(f"🚫 Filtered {blacklisted_count} blacklisted URLs")
                        logger.info(f"✅ Collected {len(urls)} URLs (target: {depth})")
                        return urls

                logger.info(f"📄 Page {page}: collected {len(organic_results)} results")

            except SerpAPIError as e:
                logger.error(f"❌ Error on page {page}: {str(e)}")
                if page == 0:
                    raise
                break

        if blacklisted_count > 0:
            logger.info(f"🚫 Total blacklisted URLs filtered: {blacklisted_count}")
        logger.info(f"✅ Total URLs collected: {len(urls)} (target: {depth})")
        return urls

    async def get_results(
        self,
        keyword: str,
        region_id: Optional[int] = None,
        depth: int = 10,
        engine: str = "yandex"
    ) -> List[str]:
        """
        Универсальный метод для получения результатов
        
        Args:
            keyword: Поисковый запрос
            region_id: ID региона из yandex_region.json
            depth: Количество результатов
            engine: Поисковая система ("yandex" или "google")
            
        Returns:
            Список URL
        """
        
        if engine == "yandex":
            return await self.get_yandex_results(keyword, region_id, depth)
        
        elif engine == "google":
            # Для Google получаем название региона
            from utils import region_manager
            
            if region_id:
                location = region_manager.get_google_location(region_id)
            else:
                location = "Russia"
            
            return await self.get_google_results(keyword, location, depth)
        
        else:
            raise ValueError(f"Unsupported engine: {engine}")
    
    def _is_blacklisted(self, url: str) -> bool:
        """
        Проверить, находится ли URL в черном списке
        
        Args:
            url: URL для проверки
            
        Returns:
            True если URL в blacklist
        """
        blacklist = settings.blacklist_domains_list
        
        if not blacklist:
            return False
        
        return any(domain in url for domain in blacklist)


# Глобальный экземпляр сервиса
serp_service = SerpService()