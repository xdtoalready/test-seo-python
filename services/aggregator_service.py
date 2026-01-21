from typing import List, Dict, Any
from collections import defaultdict
from loguru import logger

from utils.entity_matcher import entity_matcher


class AggregatorService:
    """Сервис для агрегации и подсчета частот сущностей"""
    
    def __init__(self):
        self.matcher = entity_matcher
    
    def _create_entity_key(self, entity: Dict) -> str:
        """
        Создать уникальный ключ для сущности (для группировки)
        
        Args:
            entity: Сущность
            
        Returns:
            Строковый ключ
        """
        # Нормализуем и объединяем
        e1 = self.matcher.normalize_text(entity['entity_1'])
        rel = self.matcher.normalize_text(entity['relation'])
        e2 = self.matcher.normalize_text(entity['entity_2'])
        
        return f"{e1}||{rel}||{e2}"
    
    def aggregate_entities(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Агрегировать сущности с нескольких сайтов
        
        Args:
            results: Список результатов анализа
            [
                {
                    "url": str,
                    "entities": List[Dict],
                    ...
                },
                ...
            ]
            
        Returns:
            Агрегированный список:
            [
                {
                    "entity_1": str,
                    "relation": str,
                    "entity_2": str,
                    "count": int,  # Количество сайтов где встречается
                    "urls": List[str],  # URL сайтов
                    "frequency": float,  # Процент сайтов (0.0-1.0)
                },
                ...
            ]
        """
        
        logger.info(f"📊 Aggregating entities from {len(results)} sources")
        
        # Словарь: ключ сущности -> данные
        entity_groups = defaultdict(lambda: {
            "entity_1": None,
            "relation": None,
            "entity_2": None,
            "urls": set(),
            "count": 0,
            "contexts": []
        })
        
        total_sources = len(results)
        
        # Проход по всем результатам
        for result in results:
            url = result['url']
            entities = result.get('entities', [])
            
            logger.debug(f"Processing {len(entities)} entities from {url}")
            
            for entity in entities:
                # Создать ключ
                key = self._create_entity_key(entity)
                
                # Добавить в группу
                group = entity_groups[key]
                
                # Сохранить оригинальные значения (первое вхождение)
                if group['entity_1'] is None:
                    group['entity_1'] = entity['entity_1']
                    group['relation'] = entity['relation']
                    group['entity_2'] = entity['entity_2']
                
                # Добавить URL (set автоматически исключит дубли)
                group['urls'].add(url)
                
                # Сохранить контекст
                if entity.get('context'):
                    group['contexts'].append(entity['context'])
        
        # Преобразовать в список
        aggregated = []
        
        for key, group in entity_groups.items():
            # Пропускаем если нет данных
            if group['entity_1'] is None:
                continue
            
            count = len(group['urls'])
            frequency = count / total_sources if total_sources > 0 else 0
            
            aggregated.append({
                "entity_1": group['entity_1'],
                "relation": group['relation'],
                "entity_2": group['entity_2'],
                "count": count,
                "urls": list(group['urls']),
                "frequency": frequency,
                "contexts": group['contexts'][:3]  # Берем первые 3 контекста
            })
        
        # Сортировка по частоте (важные сначала)
        aggregated.sort(key=lambda x: x['count'], reverse=True)
        
        logger.info(f"✅ Aggregated {len(aggregated)} unique entities")
        logger.info(f"   Most common: {aggregated[0]['count']} occurrences" if aggregated else "")
        
        return aggregated
    
    def filter_by_frequency(
        self,
        aggregated: List[Dict[str, Any]],
        min_count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Фильтровать сущности по минимальной частоте
        
        Args:
            aggregated: Агрегированные сущности
            min_count: Минимальное количество сайтов
            
        Returns:
            Отфильтрованный список
        """
        
        filtered = [e for e in aggregated if e['count'] >= min_count]
        
        logger.info(
            f"🔍 Filtered: {len(filtered)}/{len(aggregated)} entities "
            f"with count >= {min_count}"
        )
        
        return filtered
    
    def get_statistics(
        self,
        aggregated: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Получить статистику по агрегированным сущностям
        
        Args:
            aggregated: Агрегированные сущности
            
        Returns:
            Словарь со статистикой
        """
        
        if not aggregated:
            return {
                "total_entities": 0,
                "max_count": 0,
                "min_count": 0,
                "avg_count": 0,
                "universal_entities": 0,  # Сущности у всех
                "common_entities": 0,      # Сущности у >50%
                "rare_entities": 0         # Сущности у 1-2 сайтов
            }
        
        counts = [e['count'] for e in aggregated]
        max_count = max(counts)
        
        stats = {
            "total_entities": len(aggregated),
            "max_count": max_count,
            "min_count": min(counts),
            "avg_count": sum(counts) / len(counts),
            "universal_entities": sum(1 for c in counts if c == max_count),
            "common_entities": sum(1 for c in counts if c > max_count / 2),
            "rare_entities": sum(1 for c in counts if c <= 2)
        }
        
        logger.info(f"📈 Statistics: {stats}")
        
        return stats


# Глобальный экземпляр
aggregator_service = AggregatorService()