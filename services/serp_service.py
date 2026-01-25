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

    async def _resolve_google_location_id(
        self,
        region_id: int,
        region_title: Optional[str],
        google_query: Optional[str]
    ) -> Optional[str]:
        """
        Резолв Google location_id через Locations API с кэшированием

        Args:
            region_id: ID региона из yandex_region.json
            region_title: Название региона (для определения City/Region)
            google_query: Строка для поиска (напр. "Moscow, Russia")

        Returns:
            location_id (строка вида "585069abee19ad271e9b7352") или None
        """
        if not region_id or not google_query:
            return None

        # 1. Проверить кэш
        from services.storage_service import storage
        cache_key = f"google_loc:{region_id}"
        cached = await storage.get_kv(cache_key)
        if cached:
            logger.debug(f"📍 Location ID from cache: {region_id} -> {cached}")
            return cached

        # 2. Запрос к Locations API
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                params = {
                    "api_key": self.api_key,
                    "q": google_query,
                    "limit": 5
                }
                logger.info(f"🔍 Resolving location: query='{google_query}'")

                response = await client.get(
                    "https://serpapi.com/locations.json",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

            if not isinstance(data, list) or not data:
                logger.warning(f"⚠️ No locations found for query '{google_query}'")
                return None

            # 3. Фильтр RU локаций
            ru_locations = [loc for loc in data if loc.get("country_code") == "RU"]
            if not ru_locations:
                logger.warning(f"⚠️ No RU locations found for query '{google_query}'")
                return None

            # 4. Выбор City или Region на основе region_title
            title_lower = (region_title or "").lower()
            want_region = any(
                keyword in title_lower
                for keyword in ["область", "край", "республика", "и область", "ао", "автоном"]
            )

            preferred_type = "Region" if want_region else "City"
            logger.debug(f"📍 Preferring target_type='{preferred_type}' for '{region_title}'")

            # Искать предпочтительный тип
            preferred = next(
                (loc for loc in ru_locations if loc.get("target_type") == preferred_type),
                None
            )

            # Если не нашли - берем первый RU
            picked = preferred or ru_locations[0]
            location_id = picked.get("id")

            if not location_id:
                logger.warning(f"⚠️ No location_id in result for '{google_query}'")
                return None

            logger.info(
                f"✅ Resolved location: '{google_query}' -> {picked.get('name')} "
                f"(type={picked.get('target_type')}, id={location_id[:12]}...)"
            )

            # 5. Сохранить в кэш
            await storage.set_kv(cache_key, location_id)

            return location_id

        except Exception as e:
            logger.error(f"❌ Failed to resolve location for '{google_query}': {e}")
            return None

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
                    "no_cache": True,
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
        region_id: Optional[int] = None,
        depth: int = 10
    ) -> List[str]:
        """
        Получить результаты поиска из Google

        Args:
            keyword: Поисковый запрос
            region_id: ID региона из yandex_region.json (для резолва location_id)
            depth: Количество результатов (макс 100)

        Returns:
            Список URL из результатов поиска
        """

        logger.info(f"🔍 Fetching Google SERP: '{keyword}' (region_id={region_id or 'default'}, depth={depth})")

        # Резолв location_id если указан region_id
        location_id = None
        if region_id:
            from utils import region_manager

            region = region_manager.get_by_id(region_id)
            if region:
                google_query = region.get("google_query")
                region_title = region.get("title")

                if google_query:
                    location_id = await self._resolve_google_location_id(
                        region_id=region_id,
                        region_title=region_title,
                        google_query=google_query
                    )

                    if location_id:
                        logger.info(f"✅ Using resolved location_id: {location_id[:12]}...")
                    else:
                        logger.warning(f"⚠️ Failed to resolve location_id for region {region_id}, using fallback")
                else:
                    logger.warning(f"⚠️ No google_query for region {region_id}, using fallback")
            else:
                logger.warning(f"⚠️ Region {region_id} not found, using fallback")

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
                    "gl": "ru",  # Country code for Russia
                    "google_domain": "google.ru",  # Важно для кириллицы
                    "start": page * 10,
                    "no_cache": True,
                }

                # Использовать location_id если удалось резолвить
                if location_id:
                    params["location"] = location_id
                    logger.debug(f"📍 Using location_id: {location_id[:12]}...")
                else:
                    # Фолбэк: запрос без location, но с gl=ru и hl=ru
                    logger.debug(f"📍 Using fallback: gl=ru, hl=ru (no location)")

                # Выполнить запрос
                try:
                    data = await self._make_request(params)
                except SerpAPIError as e:
                    # Если ошибка с location_id, пробуем без него
                    if "location" in str(e).lower() and location_id:
                        logger.warning(f"⚠️ location_id '{location_id}' rejected by SerpAPI, retrying without location")
                        params.pop("location", None)
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
            # Для Google используем location_id резолвер
            return await self.get_google_results(keyword, region_id, depth)

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