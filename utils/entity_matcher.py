from typing import List, Dict, Tuple
from fuzzywuzzy import fuzz
from loguru import logger

from config import settings


class EntityMatcher:
    """Класс для нечеткого сравнения и объединения сущностей"""
    
    def __init__(self, threshold: int = None):
        """
        Args:
            threshold: Порог схожести (0-100), по умолчанию из settings
        """
        self.threshold = threshold or settings.similarity_threshold
    
    def normalize_text(self, text: str) -> str:
        """
        Нормализовать текст для сравнения
        
        Args:
            text: Исходный текст
            
        Returns:
            Нормализованный текст
        """
        # Приводим к нижнему регистру
        text = text.lower().strip()
        
        # Удаляем лишние пробелы
        import re
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def are_similar(
        self,
        text1: str,
        text2: str,
        threshold: int = None
    ) -> bool:
        """
        Проверить похожесть двух текстов
        
        Args:
            text1: Первый текст
            text2: Второй текст
            threshold: Порог схожести (опционально)
            
        Returns:
            True если тексты похожи
        """
        threshold = threshold or self.threshold
        
        # Нормализация
        text1_norm = self.normalize_text(text1)
        text2_norm = self.normalize_text(text2)
        
        # Если идентичны после нормализации
        if text1_norm == text2_norm:
            return True
        
        # Нечеткое сравнение (fuzzywuzzy)
        similarity = fuzz.ratio(text1_norm, text2_norm)
        
        return similarity >= threshold
    
    def find_similar_entity(
        self,
        entity: str,
        entity_list: List[str],
        threshold: int = None
    ) -> Tuple[str, int]:
        """
        Найти похожую сущность в списке
        
        Args:
            entity: Сущность для поиска
            entity_list: Список сущностей
            threshold: Порог схожести
            
        Returns:
            (похожая_сущность, similarity_score) или (None, 0)
        """
        threshold = threshold or self.threshold
        
        entity_norm = self.normalize_text(entity)
        
        best_match = None
        best_score = 0
        
        for candidate in entity_list:
            candidate_norm = self.normalize_text(candidate)
            
            # Точное совпадение после нормализации
            if entity_norm == candidate_norm:
                return candidate, 100
            
            # Нечеткое сравнение
            score = fuzz.ratio(entity_norm, candidate_norm)
            
            if score >= threshold and score > best_score:
                best_match = candidate
                best_score = score
        
        return best_match, best_score
    
    def entities_are_similar(
        self,
        entity1: Dict,
        entity2: Dict,
        check_relation: bool = True
    ) -> bool:
        """
        Сравнить две полные сущности (entity_1, relation, entity_2)
        
        Args:
            entity1: Первая сущность
            entity2: Вторая сущность
            check_relation: Проверять ли relation (по умолчанию True)
            
        Returns:
            True если сущности похожи
        """
        
        # Сравниваем entity_1
        if not self.are_similar(entity1['entity_1'], entity2['entity_1']):
            return False
        
        # Сравниваем entity_2
        if not self.are_similar(entity1['entity_2'], entity2['entity_2']):
            return False
        
        # Опционально сравниваем relation
        if check_relation:
            if not self.are_similar(entity1['relation'], entity2['relation']):
                return False
        
        return True


# Глобальный экземпляр
entity_matcher = EntityMatcher()