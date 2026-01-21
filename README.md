# SEO Entity Analyzer

Автоматизированный анализ семантических сущностей конкурентов для GEO/AEO продвижения.

## 🚀 Возможности

- ✅ Парсинг ТОП-10 выдачи (Яндекс, Google) через SerpAPI
- ✅ Умное извлечение контента (Trafilatura)
- ✅ ИИ-анализ сущностей (DeepSeek V3.2)
- ✅ Агрегация и подсчет частот
- ✅ Профессиональные Excel отчеты
- ✅ REST API с Swagger документацией
- ✅ Поиск регионов для Яндекс и Google
- ✅ Асинхронная обработка задач
- ✅ Docker ready

## 📋 Требования

- Docker & Docker Compose
- API ключи:
  - [SerpAPI](https://serpapi.com/) - для SERP
  - [OpenRouter](https://openrouter.ai/) - для DeepSeek V3.2

## 🏁 Быстрый старт

### 1. Клонирование
```bash
git clone <your-gitlab-repo>
cd seo-analyzer
```

### 2. Настройка .env
```bash
cp .env.example .env
```

### 3. Запуск
```bash
docker-compose up --build
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