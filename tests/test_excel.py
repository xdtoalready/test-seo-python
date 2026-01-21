import asyncio
from services import aggregator_service
from utils import excel_generator


async def test_excel_generation():
    """Тест генерации Excel отчета"""
    
    print("=" * 60)
    print("ТЕСТ EXCEL GENERATOR")
    print("=" * 60)
    
    # Тестовые данные (имитация агрегированных сущностей)
    test_entities = [
        {
            "entity_1": "Выкуп битых автомобилей",
            "relation": "осуществляется",
            "entity_2": "в Санкт-Петербурге",
            "count": 3,
            "urls": [
                "https://site1.ru",
                "https://site2.ru",
                "https://site3.ru"
            ],
            "frequency": 1.0
        },
        {
            "entity_1": "Оценка автомобиля",
            "relation": "производится",
            "entity_2": "По фото в WhatsApp",
            "count": 3,
            "urls": [
                "https://site1.ru",
                "https://site2.ru",
                "https://site3.ru"
            ],
            "frequency": 1.0
        },
        {
            "entity_1": "Компания",
            "relation": "работает",
            "entity_2": "с залоговыми автомобилями",
            "count": 2,
            "urls": [
                "https://site1.ru",
                "https://site2.ru"
            ],
            "frequency": 0.67
        },
        {
            "entity_1": "Выкуп",
            "relation": "требует",
            "entity_2": "Паспорт владельца",
            "count": 2,
            "urls": [
                "https://site2.ru",
                "https://site3.ru"
            ],
            "frequency": 0.67
        },
        {
            "entity_1": "Оплата",
            "relation": "производится",
            "entity_2": "Наличными или на карту",
            "count": 1,
            "urls": [
                "https://site1.ru"
            ],
            "frequency": 0.33
        },
    ]
    
    metadata = {
        "keyword": "выкуп битых авто",
        "region": "Санкт-Петербург",
        "total_sources": 3,
        "task_id": "test_excel_001"
    }
    
    print("\n📊 Генерация Excel отчета...")
    print(f"   Сущностей: {len(test_entities)}")
    print(f"   Источников: {metadata['total_sources']}")
    
    try:
        # Генерация отчета
        filepath = excel_generator.generate_report(
            aggregated_entities=test_entities,
            metadata=metadata,
            filename="test_report.xlsx"
        )
        
        print(f"\n✅ Отчет сгенерирован: {filepath}")
        print(f"\n📥 Скачай файл из Docker контейнера:")
        print(f"   docker cp seo-analyzer-api:/app/{filepath} .")
        
        return filepath
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    result = await test_excel_generation()
    
    if result:
        print("\n" + "=" * 60)
        print("🎉 ТЕСТ ПРОЙДЕН!")
        print("=" * 60)
    else:
        print("\n❌ Тест не пройден")


if __name__ == "__main__":
    asyncio.run(main())