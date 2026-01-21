import asyncio
from services import (
    serp_service,
    parser_service,
    llm_service,
    aggregator_service
)


async def test_full_pipeline():
    """
    Полный тест пайплайна:
    SERP → Парсинг → ИИ анализ → Агрегация
    """
    
    print("=" * 60)
    print("ПОЛНЫЙ ТЕСТ ПАЙПЛАЙНА")
    print("=" * 60)
    
    keyword = "выкуп битых авто"
    region = "Санкт-Петербург"
    depth = 3  # Только 3 сайта для теста (экономия времени)
    
    try:
        # ШАГ 1: Получить SERP
        print(f"\n🔍 ШАГ 1: Получение SERP для '{keyword}'")
        urls = await serp_service.get_yandex_results(
            keyword=keyword,
            region=region,
            depth=depth
        )
        
        print(f"✅ Найдено {len(urls)} URL\n")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")
        
        if not urls:
            print("❌ Нет URL для анализа")
            return
        
        # ШАГ 2: Извлечь контент
        print(f"\n📥 ШАГ 2: Извлечение контента ({len(urls)} страниц)")
        contents = await parser_service.extract_multiple(urls)
        
        print(f"✅ Успешно обработано {len(contents)}/{len(urls)} страниц\n")
        for content in contents:
            print(f"  • {content['url']}: {content['length']} символов")
        
        if not contents:
            print("❌ Не удалось извлечь контент")
            return
        
        # ШАГ 3: ИИ анализ (ПАРАЛЛЕЛЬНО!)
        print(f"\n🤖 ШАГ 3: ИИ анализ ({len(contents)} страниц)")
        print("⏳ Это займет ~2-5 минут...\n")
        
        # Запускаем параллельно!
        tasks = [
            llm_service.analyze_url(c['url'], c['text'])
            for c in contents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты
        analysis_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  ❌ Ошибка в задаче {i}: {result}")
                continue
            
            analysis_results.append(result)
            print(f"  ✅ {result['url']}: {result['entity_count']} сущностей")
        
        if not analysis_results:
            print("\n❌ Не удалось проанализировать ни одну страницу")
            return
        
        # ШАГ 4: Агрегация
        print(f"\n📊 ШАГ 4: Агрегация результатов")
        aggregated = aggregator_service.aggregate_entities(analysis_results)
        
        print(f"\n✅ Агрегировано {len(aggregated)} уникальных сущностей\n")
        
        # Показать ТОП-10
        print("=" * 60)
        print("ТОП-10 САМЫХ ВАЖНЫХ СУЩНОСТЕЙ")
        print("=" * 60)
        
        for i, entity in enumerate(aggregated[:10], 1):
            count = entity['count']
            freq_percent = entity['frequency'] * 100
            
            print(f"\n{i}. [{count}/{len(analysis_results)}] ({freq_percent:.0f}%)")
            print(f"   {entity['entity_1']} → {entity['relation']} → {entity['entity_2']}")
            print(f"   На сайтах: {len(entity['urls'])}")
        
        # Статистика
        print("\n" + "=" * 60)
        print("СТАТИСТИКА")
        print("=" * 60)
        
        stats = aggregator_service.get_statistics(aggregated)
        
        print(f"\nВсего уникальных сущностей: {stats['total_entities']}")
        print(f"Универсальные (у всех {len(analysis_results)} сайтов): {stats['universal_entities']}")
        print(f"Частые (у >50% сайтов): {stats['common_entities']}")
        print(f"Редкие (у 1-2 сайтов): {stats['rare_entities']}")
        print(f"Средняя частота: {stats['avg_count']:.1f}")
        
        print("\n" + "=" * 60)
        
        return aggregated
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    result = await test_full_pipeline()
    
    if result:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("\n❌ Тест не пройден")


if __name__ == "__main__":
    asyncio.run(main())