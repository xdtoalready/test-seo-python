import asyncio
from services.llm_service import llm_service


async def test_entity_extraction():
    """Тест извлечения сущностей из текста"""
    
    print("🤖 Тестирование DeepSeek V3.2...\n")
    
    # Тестовый текст (реальный пример)
    test_text = """
    Выкуп битых автомобилей в Санкт-Петербурге
    
    Купим ваш битый автомобиль быстро и дорого. Оценка по фото в WhatsApp за 15 минут.
    Работаем с любыми документами: ПТС, СТС, договор купли-продажи.
    
    Для сделки необходимы:
    - Паспорт владельца
    - ПТС или электронный ПТС
    - СТС (при наличии)
    
    Оплата наличными или на карту в день обращения. Снимаем автомобиль с учета.
    Эвакуатор бесплатно по всему городу.
    
    Работаем с залоговыми автомобилями и автомобилями в кредите.
    """
    
    try:
        print(f"📝 Анализируемый текст ({len(test_text)} символов):\n")
        print("-" * 60)
        print(test_text.strip())
        print("-" * 60)
        print("\n⏳ Отправка запроса в DeepSeek V3.2...\n")
        
        entities = await llm_service.extract_entities(test_text)
        
        print(f"\n✅ Извлечено {len(entities)} сущностей:\n")
        print("=" * 60)
        
        for i, entity in enumerate(entities, 1):
            print(f"\n{i}. {entity['entity_1']} → ({entity['relation']}) → {entity['entity_2']}")
            if entity.get('context'):
                print(f"   Контекст: {entity['context'][:100]}...")
        
        print("\n" + "=" * 60)
        
        return entities
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_full_pipeline():
    """Тест полного пайплайна: URL → Парсинг → ИИ"""
    
    print("\n\n🔄 Тестирование полного пайплайна...\n")
    
    from services.parser_service import parser_service
    
    test_url = "https://carprice.ru/kontakty/sankt-peterburg/buyout/vykup-bitykh-avto"
    
    try:
        # 1. Извлечь контент
        print(f"📥 Шаг 1: Извлечение контента из {test_url}")
        content = await parser_service.extract_content(test_url)
        
        if not content:
            print("❌ Не удалось извлечь контент")
            return None
        
        print(f"✅ Извлечено {content['length']} символов\n")
        
        # 2. Анализ с помощью ИИ
        print(f"🤖 Шаг 2: Анализ контента с DeepSeek V3.2")
        result = await llm_service.analyze_url(
            url=content['url'],
            text=content['text']
        )
        
        print(f"\n✅ Найдено {result['entity_count']} сущностей:\n")
        
        for i, entity in enumerate(result['entities'][:5], 1):  # Показываем первые 5
            print(f"{i}. {entity['entity_1']} → {entity['relation']} → {entity['entity_2']}")
        
        if len(result['entities']) > 5:
            print(f"... и еще {len(result['entities']) - 5} сущностей")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Главная функция теста"""
    
    print("=" * 60)
    print("SEO ENTITY ANALYZER - LLM SERVICE TEST")
    print("=" * 60)
    
    # Тест 1: Извлечение из тестового текста
    entities = await test_entity_extraction()
    
    # Тест 2: Полный пайплайн
    pipeline_result = await test_full_pipeline()
    
    print("\n" + "=" * 60)
    print(f"ИТОГО:")
    print(f"  Тест 1: {len(entities)} сущностей")
    print(f"  Тест 2: {pipeline_result['entity_count'] if pipeline_result else 0} сущностей")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())