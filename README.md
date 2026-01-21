# SEO Entity Analyzer

Автоматизированный анализ семантических сущностей конкурентов для GEO/AEO продвижения.

## 🚀 Возможности

- Парсинг ТОП-10 выдачи (Яндекс, Google) через SerpAPI
- Умное извлечение контента (Trafilatura)
- ИИ-анализ сущностей (DeepSeek V3.2)
- Агрегация и подсчет частот
- Профессиональные Excel отчеты
- REST API с Swagger документацией
- Поиск регионов для Яндекс и Google
- Асинхронная обработка задач
- **🎭 DEMO режим для экспертной проверки (без API ключей)**
- Docker ready

## 🎭 Режимы работы

### DEMO MODE (для экспертной проверки)
**Работает без API ключей!** Использует предзаписанные mock данные для демонстрации функциональности.

**Быстрый запуск:**
```bash
# Скопировать demo конфигурацию
cp .env.demo .env

# Запустить Docker
docker-compose up
```

**Доступ к API:**
- Swagger UI: http://localhost:8000/api/v1/docs
- Тестовый запрос (POST): http://localhost:8000/api/v1/analyze

### PRODUCTION MODE (полная функциональность)
Требуется регистрация и получение API ключей:
- [SerpAPI](https://serpapi.com/) - 100 бесплатных запросов
- [OpenRouter](https://openrouter.ai/) - $5 бесплатного кредита

**Настройка:**
```bash
# Скопировать пример конфигурации
cp .env.example .env

# Отредактировать .env:
# DEMO_MODE=false
# OPENROUTER_API_KEY=sk-or-v1-ваш_ключ
# SERPAPI_KEY=ваш_ключ

# Запустить Docker
docker-compose up
```

## 📋 Требования

- Docker & Docker Compose (обязательно)
- API ключи (только для production режима):
  - [SerpAPI](https://serpapi.com/) - для получения результатов поиска
  - [OpenRouter](https://openrouter.ai/) - для ИИ-анализа с DeepSeek V3.2

## 📋 Сравнение режимов

| Параметр | DEMO MODE | PRODUCTION MODE |
|----------|-----------|-----------------|
| API ключи | ❌ Не требуются | ✅ Требуются |
| Данные | Mock (предзаписанные) | Реальные API запросы |
| Функциональность | Полная демонстрация | Полная работа |
| Стоимость | $0 | ~$0.06 за анализ |
| Назначение | Экспертная проверка | Боевое использование |

## 📋 Различия dev/prod

| Параметр | Development | Production |
|----------|------------|------------|
| Хранилище | In-memory | Redis |
| Hot reload | ✅ Да | ❌ Нет |
| Логи | DEBUG | INFO |
| Зависимости | Только API | API + Redis |
| Restart policy | unless-stopped | always |
| Healthchecks | ❌ Нет | ✅ Да |

## 🔧 Команды
```bash
# Development
docker-compose up              # Запуск
docker-compose down            # Остановка
docker-compose logs -f         # Логи

# Production
docker-compose -f docker-compose.prod.yml up -d    # Запуск
docker-compose -f docker-compose.prod.yml down     # Остановка
docker-compose -f docker-compose.prod.yml logs -f  # Логи
```

### 4. Проверка
```
http://localhost:8000/api/v1/docs
```

## 📡 API Endpoints

### Анализ
```bash
POST /api/v1/analyze
{
  "task_id": "task_001",
  "keyword": "выкуп битых авто",
  "region_id": 213,
  "settings": {
    "depth": 10,
    "engine": "yandex"
  }
}
```

### Поиск регионов
```bash
GET /api/v1/regions/search?q=Моск
```

### Статус задачи
```bash
GET /api/v1/status/{task_id}
```

### Скачать отчет
```bash
GET /api/v1/download/{task_id}
```

## 🔧 Production Setup

### С Redis и PostgreSQL (донастройка)

1. Раскомментировать сервисы в `docker-compose.yml`
2. Обновить `services/storage_service.py`
3. Перезапустить контейнеры

## 💰 Стоимость

~$0.06 за анализ (5 сайтов):
- SerpAPI: $0.006
- DeepSeek V3.2: ~$0.05

## 📚 Документация

- API Docs: `http://localhost:8000/api/v1/docs`
- Regions JSON: `yandex_region.json`