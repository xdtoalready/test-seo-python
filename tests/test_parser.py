import asyncio
from services.parser_service import parser_service


async def test_single_url():
    """Тест парсинга одного URL"""
    
    print("🔍 Тестирование парсинга одного URL...\n")
    
    # Возьмем URL из предыдущего теста
    test_url = "https://carprice.ru/kontakty/sankt-peterburg/buyout/vykup-bitykh-avto"
    
    try:
        result = await parser_service.extract_content(test_url)
        
        if result:
            print(f"✅ URL: {result['url']}")
            print(f"✅ Длина текста: {result['length']} символов")
            print(f"✅ Обрезан: {result['truncated']}")
            print(f"\n📝 Первые 500 символов:\n")
            print("-" * 60)
            print(result['text'][:500])
            print("-" * 60)
            
            return result
        else:
            print("❌ Не удалось извлечь контент")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


async def test_multiple_urls():
    """Тест параллельного парсинга нескольких URL"""
    
    print("\n\n🔍 Тестирование параллельного парсинга...\n")
    
    test_urls = [
        "https://carprice.ru/kontakty/sankt-peterburg/buyout/vykup-bitykh-avto",
        "https://bitcar.spb.ru/",
        "https://skupka-auto.su/vykup_avto_v_samare/"
    ]
    
    try:
        results = await parser_service.extract_multiple(test_urls)
        
        print(f"\n✅ Обработано {len(results)}/{len(test_urls)} URL\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['url']}")
            print(f"   Длина: {result['length']} символов")
            print(f"   Обрезан: {result['truncated']}\n")
        
        return results
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []


async def main():
    """Главная функция теста"""
    
    print("=" * 60)
    print("SEO ENTITY ANALYZER - PARSER SERVICE TEST")
    print("=" * 60)
    
    # Тест одного URL
    single_result = await test_single_url()
    
    # Тест нескольких URL
    multiple_results = await test_multiple_urls()
    
    print("\n" + "=" * 60)
    print(f"ИТОГО: Успешно обработано {len(multiple_results)} URL")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())