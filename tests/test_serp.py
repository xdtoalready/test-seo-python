import asyncio
from services.serp_service import serp_service


async def test_yandex():
    """Тест получения результатов из Яндекса"""
    
    print("🔍 Тестирование Yandex SERP...\n")
    
    try:
        urls = await serp_service.get_yandex_results(
            keyword="выкуп битых авто",
            region="Москва",
            depth=5  # Берем только 5 для теста
        )
        
        print(f"\n✅ Получено {len(urls)} URL:\n")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
        
        return urls
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return []


async def test_google():
    """Тест получения результатов из Google"""
    
    print("\n\n🔍 Тестирование Google SERP...\n")
    
    try:
        urls = await serp_service.get_google_results(
            keyword="выкуп битых авто",
            region="ru",
            depth=5
        )
        
        print(f"\n✅ Получено {len(urls)} URL:\n")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
        
        return urls
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return []


async def main():
    """Главная функция теста"""
    
    print("=" * 60)
    print("SEO ENTITY ANALYZER - SERP SERVICE TEST")
    print("=" * 60)
    
    # Тест Яндекс
    yandex_urls = await test_yandex()
    
    # Тест Google
    google_urls = await test_google()
    
    print("\n" + "=" * 60)
    print(f"ИТОГО: Яндекс={len(yandex_urls)}, Google={len(google_urls)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())