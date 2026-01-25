import json
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger


class RegionManager:
    """Менеджер регионов для поисковых систем"""
    
    def __init__(self, json_path: str = "yandex_region.json"):
        """
        Args:
            json_path: Путь к JSON файлу с регионами
        """
        self.json_path = Path(json_path)
        self.regions: List[Dict] = []
        self._load_regions()
    
    def _load_regions(self):
        """Загрузить регионы из JSON файла"""
        try:
            if not self.json_path.exists():
                logger.error(f"❌ Region file not found: {self.json_path}")
                self.regions = []
                return
            
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.regions = json.load(f)
            
            logger.info(f"✅ Loaded {len(self.regions)} regions from {self.json_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load regions: {e}")
            self.regions = []
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Поиск регионов по названию (автокомплит)
        
        Args:
            query: Поисковый запрос
            limit: Максимум результатов
            
        Returns:
            Список регионов [{"id": int, "title": str, "parent": int}, ...]
        """
        if not query or len(query) < 2:
            return []
        
        query_lower = query.lower()
        
        # Поиск по началу названия (приоритет)
        starts_with = [
            r for r in self.regions
            if r['title'].lower().startswith(query_lower)
        ]
        
        # Поиск по вхождению в середине
        contains = [
            r for r in self.regions
            if query_lower in r['title'].lower() and r not in starts_with
        ]
        
        results = starts_with + contains
        
        return results[:limit]
    
    def get_by_id(self, region_id: int) -> Optional[Dict]:
        """
        Получить регион по ID
        
        Args:
            region_id: ID региона
            
        Returns:
            Регион или None
        """
        for region in self.regions:
            if region['id'] == region_id:
                return region
        return None
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        """
        Получить регион по точному названию
        
        Args:
            name: Название региона
            
        Returns:
            Регион или None
        """
        name_lower = name.lower()
        for region in self.regions:
            if region['title'].lower() == name_lower:
                return region
        return None
    
    def get_yandex_lr(self, region_id: int) -> Optional[int]:
        """
        Получить Яндекс lr параметр (region_id)
        
        Args:
            region_id: ID региона
            
        Returns:
            ID региона для Яндекс (lr параметр)
        """
        region = self.get_by_id(region_id)
        return region['id'] if region else None
    
    def get_google_query(self, region_id: int) -> Optional[str]:
        """
        Получить google_query для резолва location через Locations API

        Args:
            region_id: ID региона

        Returns:
            Строка для запроса к Locations API или None
        """
        region = self.get_by_id(region_id)
        return region.get("google_query") if region else None

    def get_google_location(self, region_id: int) -> str:
        """
        Получить Google location параметр (название региона)

        Args:
            region_id: ID региона

        Returns:
            Название региона для Google или "Russia" как фолбэк

        DEPRECATED: Используйте get_google_query() + resolve_location_id()
        """
        region = self.get_by_id(region_id)

        if not region:
            return "Russia"

        # Возвращаем google_query вместо title (кириллица не работает)
        return region.get('google_query', region['title'])


# Глобальный экземпляр
region_manager = RegionManager()