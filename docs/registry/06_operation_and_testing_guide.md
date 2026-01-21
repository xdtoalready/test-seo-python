# Руководство по эксплуатации и тестированию программного обеспечения SEO Entity Analyzer

**Версия ПО:** 1.0.0
**Дата составления:** 21.01.2026
**Назначение:** Инструкция для экспертной проверки и эксплуатации

---

## Содержание

1. [Введение](#1-введение)
2. [Быстрый старт для экспертов](#2-быстрый-старт-для-экспертов)
3. [Тестовые сценарии](#3-тестовые-сценарии)
4. [Проверка функциональности](#4-проверка-функциональности)
5. [Эксплуатация в рабочем режиме](#5-эксплуатация-в-рабочем-режиме)
6. [Мониторинг и диагностика](#6-мониторинг-и-диагностика)
7. [Типичные операции](#7-типичные-операции)
8. [Контрольные чек-листы](#8-контрольные-чек-листы)

---

## 1. Введение

### 1.1. Назначение документа

Данное руководство предназначено для:
- **Экспертов** - проведение экспертной проверки функциональности ПО
- **Администраторов** - эксплуатация и обслуживание ПО
- **Пользователей** - практическое использование системы

### 1.2. Краткое описание ПО

**SEO Entity Analyzer** - программное обеспечение для анализа конкурентов в поисковой выдаче. Система автоматически:
1. Получает топ-10 сайтов из поисковых систем (Яндекс/Google)
2. Извлекает текстовый контент с этих сайтов
3. Анализирует контент с помощью ИИ (DeepSeek V3.2)
4. Извлекает семантические сущности и связи между ними
5. Генерирует Excel отчет с агрегированными данными

### 1.3. Два режима работы

**DEMO MODE** (для экспертизы):
- Не требует API ключей
- Использует предзаписанные данные
- Полная демонстрация функциональности
- Время выполнения: ~5 секунд

**PRODUCTION MODE** (для реальной работы):
- Требует API ключи (SerpAPI, OpenRouter)
- Работает с реальными данными
- Актуальная информация из интернета
- Время выполнения: 30-60 секунд

---

## 2. Быстрый старт для экспертов

### 2.1. Предварительные требования

Убедитесь, что у вас установлен Docker:
```bash
docker --version
# Ожидается: Docker version 20.10 или выше
```

Если Docker не установлен, см. документ `03_installation_guide.md`

### 2.2. Запуск в DEMO режиме (5 минут)

**Шаг 1: Скачать и распаковать архив**
```bash
# Если предоставлен архив
tar -xzf seo-entity-analyzer-1.0.0.tar.gz
cd seo-entity-analyzer-1.0.0

# ИЛИ скачать Docker образ
docker pull seo-entity-analyzer:1.0.0
mkdir seo-analyzer-demo && cd seo-analyzer-demo
```

**Шаг 2: Создать конфигурацию**
```bash
# Скопировать готовую demo конфигурацию
cp .env.demo .env

# ИЛИ создать вручную
cat > .env << 'EOF'
DEMO_MODE=true
OPENROUTER_API_KEY=
SERPAPI_KEY=
ENVIRONMENT=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
STORAGE_BACKEND=memory
EOF
```

**Шаг 3: Создать docker-compose.yml**
```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  api:
    image: seo-entity-analyzer:1.0.0
    container_name: seo-analyzer
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./reports:/app/reports
    restart: unless-stopped
EOF
```

**Шаг 4: Запустить**
```bash
docker-compose up -d
```

**Шаг 5: Проверить запуск**
```bash
# Просмотр логов (должна быть надпись "DEMO MODE")
docker-compose logs -f

# Ожидается:
# 🎭 DEMO MODE: Using mock SERP data
# 🎭 DEMO MODE: Using mock LLM data
# 🎭 DEMO MODE: Using mock parser data
# 🚀 Starting SEO Entity Analyzer API
# Application startup complete

# Ctrl+C для выхода из логов
```

**Шаг 6: Открыть веб-интерфейс**
```
http://localhost:8000/api/v1/docs
```

Вы увидите интерактивную документацию API (Swagger UI).

### 2.3. Первый тестовый запрос (1 минута)

**Через браузер (Swagger UI):**
1. Открыть http://localhost:8000/api/v1/docs
2. Найти endpoint `POST /api/v1/analyze`
3. Нажать "Try it out"
4. Ввести данные:
```json
{
  "task_id": "expert-test-001",
  "keyword": "выкуп битых автомобилей москва",
  "region_id": 213,
  "settings": {
    "depth": 10,
    "engine": "yandex"
  }
}
```
5. Нажать "Execute"
6. Увидеть ответ:
```json
{
  "task_id": "expert-test-001",
  "status": "queued",
  "message": "Задача 'expert-test-001' поставлена в очередь"
}
```

**Через curl (командная строка):**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "expert-test-001",
    "keyword": "выкуп битых автомобилей москва",
    "region_id": 213,
    "settings": {"depth": 10, "engine": "yandex"}
  }'
```

### 2.4. Проверка результата

**Подождать 5-10 секунд, затем проверить статус:**

Через браузер:
1. Найти endpoint `GET /api/v1/status/{task_id}`
2. Ввести: `expert-test-001`
3. Нажать "Execute"

Через curl:
```bash
curl http://localhost:8000/api/v1/status/expert-test-001
```

**Ожидаемый ответ (когда готово):**
```json
{
  "task_id": "expert-test-001",
  "status": "completed",
  "progress": 100,
  "message": "Анализ завершен",
  "results": {
    "total_entities": 10,
    "total_sources": 3,
    "universal_entities": 2,
    "common_entities": 3,
    "rare_entities": 5,
    "excel_file": "expert-test-001.xlsx"
  }
}
```

**Скачать Excel отчет:**

Через браузер:
```
http://localhost:8000/api/v1/download/expert-test-001
```

Через curl:
```bash
curl -O http://localhost:8000/api/v1/download/expert-test-001
```

Откроется файл `expert-test-001.xlsx` с результатами анализа.

---

## 3. Тестовые сценарии

### 3.1. Тестовый сценарий №1: Базовая функциональность

**Цель:** Проверить основной цикл работы системы

**Предусловия:**
- ПО запущено в DEMO режиме
- API доступен

**Шаги:**
1. Отправить запрос на анализ с task_id = "test-scenario-1"
2. Проверить получение ответа "queued"
3. Подождать 10 секунд
4. Проверить статус задачи
5. Убедиться что status = "completed"
6. Скачать Excel отчет
7. Открыть отчет и проверить наличие данных

**Ожидаемый результат:**
- ✅ Задача выполнена успешно (status = completed)
- ✅ Excel файл содержит 5 листов (Сводка, Все сущности, Универсальные, Частые, Редкие)
- ✅ В отчете есть минимум 5 сущностей
- ✅ Метаданные содержат keyword, region, дату

**Критерии прохождения:**
- Все шаги выполнены без ошибок
- Отчет сгенерирован корректно

### 3.2. Тестовый сценарий №2: Параллельные запросы

**Цель:** Проверить обработку нескольких задач одновременно

**Предусловия:**
- ПО запущено в DEMO режиме

**Шаги:**
1. Отправить 3 запроса с разными task_id:
   - test-parallel-1
   - test-parallel-2
   - test-parallel-3
2. Проверить что все 3 задачи приняты (status = queued)
3. Подождать 15 секунд
4. Проверить статус всех 3 задач
5. Убедиться что все завершились успешно

**Ожидаемый результат:**
- ✅ Все 3 задачи выполнены успешно
- ✅ Каждая задача имеет свой Excel отчет
- ✅ Нет конфликтов между задачами

**Критерии прохождения:**
- 3 из 3 задач завершены со статусом "completed"

### 3.3. Тестовый сценарий №3: Проверка API endpoints

**Цель:** Проверить все основные API endpoints

**Таблица проверки:**

| Endpoint | Метод | Параметры | Ожидаемый код | Проверить |
|----------|-------|-----------|---------------|-----------|
| /health | GET | - | 200 | status: "ok" |
| /api/v1/health | GET | - | 200 | status: "ok" |
| /api/v1/analyze | POST | Valid request | 200 | task_id в ответе |
| /api/v1/analyze | POST | Invalid request | 422 | Ошибка валидации |
| /api/v1/status/{task_id} | GET | Existing task | 200 | Правильный статус |
| /api/v1/status/{task_id} | GET | Non-existing task | 404 | "Task not found" |
| /api/v1/download/{task_id} | GET | Completed task | 200 | Файл .xlsx |
| /api/v1/download/{task_id} | GET | Pending task | 400 | "not completed yet" |
| /api/v1/regions/search | GET | q=Моск | 200 | Список регионов |
| /api/v1/regions/213 | GET | - | 200 | region: "Москва" |

**Команды для проверки:**
```bash
# Health check
curl http://localhost:8000/health

# Invalid request (нет task_id)
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"keyword": "test"}'
# Ожидается: 422 Unprocessable Entity

# Non-existing task
curl http://localhost:8000/api/v1/status/non-existing-task
# Ожидается: 404 Not Found

# Region search
curl "http://localhost:8000/api/v1/regions/search?q=Моск"

# Region by ID
curl http://localhost:8000/api/v1/regions/213
```

### 3.4. Тестовый сценарий №4: Стресс-тест (опционально)

**Цель:** Проверить поведение под нагрузкой

**Предусловия:**
- Установлен `curl` или `ab` (Apache Bench)

**Нагрузка:**
10 запросов параллельно

```bash
# Простой скрипт
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d "{\"task_id\": \"load-test-$i\", \"keyword\": \"test\", \"region_id\": 213, \"settings\": {\"depth\": 10, \"engine\": \"yandex\"}}" &
done
wait

# Проверить что все задачи обработаны
for i in {1..10}; do
  curl http://localhost:8000/api/v1/status/load-test-$i | grep -o '"status":"[^"]*"'
done
```

**Ожидаемый результат:**
- ✅ Все запросы приняты (status 200)
- ✅ Нет ошибок 500 (Internal Server Error)
- ✅ Все задачи в итоге завершаются успешно

---

## 4. Проверка функциональности

### 4.1. Проверка компонента получения SERP

**Что проверяем:** Модуль получает список URL из поисковых систем

**Как проверить:**
1. Отправить запрос на анализ
2. Посмотреть логи:
```bash
docker logs seo-analyzer | grep "SERP"
```

**Ожидаемые записи в логах (DEMO режим):**
```
🎭 DEMO MODE: Returning mock SERP results for 'выкуп битых автомобилей'
✅ Found 10 URLs
```

**Ожидаемые записи в логах (PRODUCTION режим):**
```
🔍 Fetching Yandex SERP: 'выкуп битых автомобилей' (region_id=213, depth=10)
✅ Collected 10 URLs (target: 10)
```

### 4.2. Проверка компонента парсинга

**Что проверяем:** Модуль извлекает текст с веб-страниц

**Как проверить:**
```bash
docker logs seo-analyzer | grep "Processing:"
```

**Ожидаемые записи (DEMO режим):**
```
🎭 DEMO MODE: Returning mock parser data for 10 URLs
```

**Ожидаемые записи (PRODUCTION режим):**
```
📄 Processing: https://example.com/
✅ Extracted 3500 chars from https://example.com/
📦 Processing 10 URLs...
✅ Successfully processed 8/10 URLs
```

### 4.3. Проверка компонента ИИ-анализа

**Что проверяем:** Модуль извлекает сущности с помощью LLM

**Как проверить:**
```bash
docker logs seo-analyzer | grep "Analyzing\|entities"
```

**Ожидаемые записи (DEMO режим):**
```
🎭 DEMO MODE: Returning mock entities for text (3500 chars)
✅ Extracted 10 valid entities
```

**Ожидаемые записи (PRODUCTION режим):**
```
🤖 Analyzing text with DeepSeek V3.2 (3500 chars)...
✅ Extracted 15 valid entities
```

### 4.4. Проверка компонента агрегации

**Что проверяем:** Модуль объединяет результаты и считает статистику

**Как проверить:**
```bash
docker logs seo-analyzer | grep "Aggregat"
```

**Ожидаемые записи:**
```
📊 Step 4: Aggregating entities
✅ Aggregated 25 unique entities
```

**Дополнительная проверка:** Открыть Excel отчет, лист "Сводка", проверить:
- Total entities > 0
- Universal + Common + Rare = Total entities

### 4.5. Проверка генерации Excel отчета

**Что проверяем:** Модуль создает корректный Excel файл

**Как проверить:**
1. Скачать отчет
2. Открыть в Excel / LibreOffice Calc
3. Проверить структуру:
   - 5 листов: Сводка, Все сущности, Универсальные, Частые, Редкие
   - Лист "Сводка" содержит метаданные
   - Лист "Все сущности" содержит таблицу с колонками:
     - Entity 1
     - Relation
     - Entity 2
     - Sources Count
     - Category
     - Sources

**Ожидаемый результат:**
- ✅ Файл открывается без ошибок
- ✅ Все 5 листов присутствуют
- ✅ Данные корректно отформатированы
- ✅ Ширина столбцов подобрана автоматически

---

## 5. Эксплуатация в рабочем режиме

### 5.1. Переключение на PRODUCTION режим

**Требования:**
- Зарегистрированы аккаунты в SerpAPI и OpenRouter
- Получены API ключи

**Процедура:**
1. Остановить контейнер:
```bash
docker-compose down
```

2. Отредактировать .env:
```bash
nano .env
# Изменить:
# DEMO_MODE=false
# OPENROUTER_API_KEY=sk-or-v1-ваш_ключ
# SERPAPI_KEY=ваш_ключ
```

3. Перезапустить:
```bash
docker-compose up -d
```

4. Проверить логи:
```bash
docker logs seo-analyzer | head -20
# Должно быть:
# ✅ SERPAPI_KEY configured
# ✅ OPENROUTER_API_KEY configured
# 🚀 Starting in production mode
```

### 5.2. Типичный рабочий процесс

**Сценарий использования:**
Маркетолог хочет проанализировать конкурентов по запросу "ремонт квартир москва"

**Шаги:**
1. Открыть http://localhost:8000/api/v1/docs
2. Найти регион через `/api/v1/regions/search?q=Москва`
3. Запустить анализ через `/api/v1/analyze`:
```json
{
  "task_id": "repair-moscow-20260121",
  "keyword": "ремонт квартир москва",
  "region_id": 213,
  "settings": {
    "depth": 10,
    "engine": "yandex"
  }
}
```
4. Подождать 30-60 секунд
5. Проверить статус через `/api/v1/status/repair-moscow-20260121`
6. Скачать отчет через `/api/v1/download/repair-moscow-20260121`
7. Открыть Excel, проанализировать:
   - Какие сущности универсальные (70%+ сайтов)
   - Какие редкие (недооцененные темы)
   - Какие связи между сущностями

**Результат:** Маркетолог получает список тем и подтем для создания контента на своем сайте.

### 5.3. Рекомендуемые настройки

**Для быстрого анализа:**
```json
{
  "depth": 5,
  "engine": "yandex"
}
```
- Время: ~20 секунд
- Стоимость: ~$0.03

**Для глубокого анализа:**
```json
{
  "depth": 20,
  "engine": "yandex"
}
```
- Время: ~2 минуты
- Стоимость: ~$0.12

**Для сравнения поисковых систем:**
Запустить 2 задачи с одинаковым keyword, но разными engine:
- engine: "yandex"
- engine: "google"

---

## 6. Мониторинг и диагностика

### 6.1. Просмотр логов

**Вся история логов:**
```bash
docker logs seo-analyzer
```

**Последние 50 строк:**
```bash
docker logs --tail 50 seo-analyzer
```

**В реальном времени:**
```bash
docker logs -f seo-analyzer
```

**За последние 24 часа:**
```bash
docker logs --since 24h seo-analyzer
```

**Поиск ошибок:**
```bash
docker logs seo-analyzer | grep -i "error\|fail"
```

### 6.2. Проверка состояния контейнера

**Статус:**
```bash
docker ps | grep seo-analyzer
# СТАТУС должен быть: Up X minutes/hours
```

**Потребление ресурсов:**
```bash
docker stats seo-analyzer --no-stream
# Проверить CPU%, MEM USAGE
```

**Детальная информация:**
```bash
docker inspect seo-analyzer
```

### 6.3. Проверка файлов

**Логи на диске:**
```bash
ls -lh logs/
cat logs/app.log | tail -100
```

**Сгенерированные отчеты:**
```bash
ls -lh reports/
# Список всех .xlsx файлов
```

**Размер данных:**
```bash
du -sh logs/ reports/
```

### 6.4. Диагностика проблем

**Контейнер не запускается:**
```bash
# Посмотреть последние логи
docker logs seo-analyzer

# Проверить конфигурацию
cat .env

# Проверить docker-compose.yml
cat docker-compose.yml

# Проверить занятость порта 8000
netstat -tulpn | grep 8000  # Linux
netstat -ano | findstr :8000  # Windows
```

**Медленная работа:**
```bash
# Проверить ресурсы
docker stats seo-analyzer

# Если CPU 100% - возможно слишком много параллельных задач
# Если MEMORY близко к лимиту - увеличить в docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 4G
```

**Ошибки API:**
```bash
# Проверить логи на наличие "401 Unauthorized" или "429 Too Many Requests"
docker logs seo-analyzer | grep -E "401|429"

# 401 - неправильные API ключи
# 429 - превышен лимит запросов
```

---

## 7. Типичные операции

### 7.1. Остановка ПО

```bash
# Остановить контейнер (с возможностью перезапуска)
docker-compose stop

# Остановить и удалить контейнер
docker-compose down
```

### 7.2. Перезапуск ПО

```bash
# Перезапустить контейнер
docker-compose restart

# ИЛИ остановить и запустить заново
docker-compose down
docker-compose up -d
```

### 7.3. Просмотр конфигурации

```bash
# Просмотр переменных окружения
docker exec seo-analyzer env | grep -E "DEMO_MODE|API_KEY"

# Просмотр версии Python и библиотек
docker exec seo-analyzer python --version
docker exec seo-analyzer pip list
```

### 7.4. Очистка данных

**Удалить старые логи:**
```bash
# Логи старше 30 дней
find logs/ -name "*.log" -mtime +30 -delete
```

**Удалить старые отчеты:**
```bash
# Отчеты старше 90 дней
find reports/ -name "*.xlsx" -mtime +90 -delete
```

**Полная очистка:**
```bash
# Остановить контейнер
docker-compose down

# Удалить все данные
rm -rf logs/ reports/

# Пересоздать директории
mkdir logs reports
```

### 7.5. Обновление ПО

```bash
# Остановить текущую версию
docker-compose down

# Скачать новую версию
docker pull seo-entity-analyzer:1.1.0

# Обновить тег в docker-compose.yml
# image: seo-entity-analyzer:1.1.0

# Запустить новую версию
docker-compose up -d

# Проверить версию
curl http://localhost:8000/health | grep version
```

---

## 8. Контрольные чек-листы

### 8.1. Чек-лист для экспертной проверки

**Предварительная проверка:**
- [ ] Docker установлен и запущен
- [ ] Порт 8000 свободен
- [ ] Достаточно места на диске (минимум 2 GB)

**Установка:**
- [ ] Docker образ загружен или собран
- [ ] Файл .env создан с DEMO_MODE=true
- [ ] Файл docker-compose.yml создан
- [ ] Контейнер запущен без ошибок

**Функциональная проверка:**
- [ ] Health endpoint отвечает (GET /health)
- [ ] Swagger UI открывается (GET /api/v1/docs)
- [ ] Запрос на анализ принят (POST /api/v1/analyze)
- [ ] Статус задачи возвращается (GET /api/v1/status/{task_id})
- [ ] Задача завершается со статусом "completed"
- [ ] Excel отчет скачивается (GET /api/v1/download/{task_id})
- [ ] Отчет открывается и содержит данные
- [ ] Поиск регионов работает (GET /api/v1/regions/search)

**Дополнительные проверки:**
- [ ] Логи не содержат критичных ошибок
- [ ] Параллельные запросы обрабатываются
- [ ] API возвращает корректные коды ошибок (404, 422)
- [ ] Контейнер стабильно работает (не падает)

**Итоговая оценка:**
- Всего пунктов: 19
- Пройдено: ____
- Процент успешности: ____%

**Критерий успешной проверки:** 100% (все 19 пунктов)

### 8.2. Чек-лист для production развертывания

**Подготовка:**
- [ ] Получены API ключи SerpAPI
- [ ] Получены API ключи OpenRouter
- [ ] Проверен баланс API (trial кредиты доступны)
- [ ] Сервер соответствует минимальным требованиям
- [ ] Установлен Docker

**Конфигурация:**
- [ ] Файл .env создан с DEMO_MODE=false
- [ ] API ключи корректно указаны в .env
- [ ] docker-compose.yml настроен
- [ ] Настроены volumes для логов и отчетов
- [ ] Настроен restart policy

**Запуск:**
- [ ] Контейнер запущен: docker-compose up -d
- [ ] Логи показывают "production mode"
- [ ] Health check проходит успешно
- [ ] Тестовый запрос (реальный) выполнен успешно

**Безопасность:**
- [ ] Файл .env имеет права доступа 600
- [ ] .env добавлен в .gitignore
- [ ] API ключи не логируются
- [ ] Доступ к порту 8000 ограничен (firewall)

**Мониторинг:**
- [ ] Настроены алерты на ошибки
- [ ] Настроен мониторинг ресурсов
- [ ] Настроена ротация логов
- [ ] Настроено резервное копирование данных

**Документация:**
- [ ] Задокументированы учетные данные (в секьюрном месте)
- [ ] Задокументированы процедуры восстановления
- [ ] Создан runbook для типичных проблем
- [ ] Команда обучена работе с ПО

**Итоговая оценка:**
- Всего пунктов: 23
- Пройдено: ____
- Процент готовности: ____%

**Критерий готовности к production:** >90% (минимум 21 пункт)

---

## 9. Заключение

Данное руководство содержит всю необходимую информацию для:
- ✅ Быстрого запуска в demo режиме (5 минут)
- ✅ Проведения экспертной проверки (30 минут)
- ✅ Развертывания в production (1 час)
- ✅ Эксплуатации и обслуживания

**Для экспертов:** Следуйте разделу 2 "Быстрый старт" и разделу 3 "Тестовые сценарии" для проведения проверки.

**Для администраторов:** Используйте разделы 5-7 для эксплуатации, мониторинга и обслуживания системы.

**Техническая поддержка:**
- Email: support@example.com
- Документация: См. другие документы в папке `docs/registry/`

---

**Дата составления:** 21.01.2026
**Подпись ответственного лица:** _________________
