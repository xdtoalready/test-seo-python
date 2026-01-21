# Документация по техническим средствам активации, выпуска, распространения и управления лицензионными ключами

**Программное обеспечение:** SEO Entity Analyzer
**Версия:** 1.0.0
**Дата составления:** 21.01.2026

---

## 1. Общие сведения о лицензировании

### 1.1. Модель лицензирования

**Тип лицензии:** Свободная лицензия (Open Source) / Проприетарная лицензия

**Особенности:**
- ПО распространяется в виде Docker образов
- Не требует аппаратной привязки (dongle, TPM)
- Не требует онлайн-активации
- Работает на любой системе с Docker

**Важная особенность данного ПО:**
Программное обеспечение само по себе не требует лицензионных ключей для запуска. Однако для полноценной работы требуются **API ключи внешних сервисов**:
- SerpAPI - для получения результатов поиска
- OpenRouter - для ИИ-анализа текстов

Эти ключи **не являются лицензионными ключами самого ПО**, а представляют собой учетные данные для доступа к внешним API, которые пользователь получает самостоятельно.

---

## 2. Технические средства активации

### 2.1. Режимы работы ПО

Программное обеспечение поддерживает два режима работы:

#### 2.1.1. DEMO MODE (Демонстрационный режим)
**Назначение:** Экспертная проверка, тестирование, демонстрация функциональности

**Активация:**
```bash
# В файле .env установить:
DEMO_MODE=true
```

**Характеристики:**
- ✅ Не требует API ключей
- ✅ Использует предзаписанные mock данные
- ✅ Полная демонстрация функциональности
- ✅ Бесплатно
- ❌ Не работает с реальными данными

#### 2.1.2. PRODUCTION MODE (Рабочий режим)
**Назначение:** Боевое использование с реальными данными

**Активация:**
```bash
# В файле .env установить:
DEMO_MODE=false
SERPAPI_KEY=ваш_ключ_serpapi
OPENROUTER_API_KEY=ваш_ключ_openrouter
```

**Характеристики:**
- ✅ Работает с реальными API
- ✅ Актуальные данные из поисковых систем
- ✅ Реальный ИИ-анализ
- ⚠️ Требует регистрации в SerpAPI и OpenRouter
- ⚠️ Платные API (с бесплатными trial версиями)

### 2.2. Процесс активации

**Шаг 1: Установка программного обеспечения**
```bash
# Получение Docker образа
docker pull seo-entity-analyzer:1.0.0

# ИЛИ сборка из исходного кода
docker build -t seo-entity-analyzer:1.0.0 .
```

**Шаг 2: Выбор режима работы**

Для DEMO режима (без API ключей):
```bash
# Скопировать готовую конфигурацию
cp .env.demo .env

# Запустить контейнер
docker-compose up
```

Для PRODUCTION режима:
```bash
# Скопировать шаблон
cp .env.example .env

# Отредактировать .env и указать:
# DEMO_MODE=false
# SERPAPI_KEY=<ваш ключ>
# OPENROUTER_API_KEY=<ваш ключ>

# Запустить контейнер
docker-compose up
```

**Шаг 3: Проверка активации**
```bash
# Открыть API документацию
http://localhost:8000/api/v1/docs

# Проверить health endpoint
curl http://localhost:8000/health
```

### 2.3. Технические средства проверки режима работы

**При запуске в логах отображается:**

DEMO режим:
```
🎭 DEMO MODE: Using mock SERP data
🎭 DEMO MODE: Using mock LLM data
🎭 DEMO MODE: Using mock parser data
```

PRODUCTION режим:
```
✅ SERPAPI_KEY configured
✅ OPENROUTER_API_KEY configured
🚀 Starting in production mode
```

---

## 3. Технические средства выпуска

### 3.1. Процесс выпуска релиза

**Этап 1: Подготовка исходного кода**
```bash
# Обновление версии в файлах
echo "VERSION=1.0.0" > version.txt

# Коммит изменений
git commit -am "Release version 1.0.0"

# Создание тега версии
git tag -a v1.0.0 -m "Release version 1.0.0"

# Отправка в репозиторий
git push origin v1.0.0
```

**Этап 2: Сборка Docker образа**
```bash
# Сборка образа с тегом версии
docker build -t seo-entity-analyzer:1.0.0 .

# Пометка как latest
docker tag seo-entity-analyzer:1.0.0 seo-entity-analyzer:latest
```

**Этап 3: Публикация**
```bash
# Авторизация в Docker Registry
docker login registry.example.com

# Загрузка образа
docker push seo-entity-analyzer:1.0.0
docker push seo-entity-analyzer:latest
```

### 3.2. Версионирование

**Схема версионирования:** Semantic Versioning (MAJOR.MINOR.PATCH)

Примеры:
- `1.0.0` - первый релиз
- `1.0.1` - исправление ошибок
- `1.1.0` - новая функциональность (обратно совместимая)
- `2.0.0` - breaking changes

### 3.3. Каналы распространения

| Канал | Описание | URL |
|-------|----------|-----|
| Docker Hub | Публичный реестр | hub.docker.com/r/username/seo-entity-analyzer |
| GitLab Registry | Встроенный реестр GitLab | registry.gitlab.com/username/seo-entity-analyzer |
| Приватный Registry | Корпоративный реестр | registry.company.local/seo-entity-analyzer |

---

## 4. Технические средства распространения

### 4.1. Методы распространения

#### 4.1.1. Docker Registry (Основной метод)

**Преимущества:**
- Автоматическая проверка целостности
- Версионирование через теги
- Быстрое развертывание
- Поддержка разных архитектур (amd64, arm64)

**Получение:**
```bash
# Скачать конкретную версию
docker pull seo-entity-analyzer:1.0.0

# Скачать последнюю версию
docker pull seo-entity-analyzer:latest
```

#### 4.1.2. Архив исходного кода

**Формат:** `.tar.gz` или `.zip`

**Получение:**
```bash
# Экспорт из Git
git archive --format=tar.gz --output=seo-entity-analyzer-1.0.0.tar.gz v1.0.0

# Распаковка
tar -xzf seo-entity-analyzer-1.0.0.tar.gz
cd seo-entity-analyzer-1.0.0

# Сборка
docker build -t seo-entity-analyzer:1.0.0 .
```

#### 4.1.3. Docker Image Export (Офлайн распространение)

**Для систем без доступа к интернету:**
```bash
# Экспорт образа в файл
docker save seo-entity-analyzer:1.0.0 -o seo-entity-analyzer-1.0.0.tar

# Передача файла на целевую систему (USB, сеть)

# Импорт на целевой системе
docker load -i seo-entity-analyzer-1.0.0.tar

# Проверка
docker images | grep seo-entity-analyzer
```

### 4.2. Контроль целостности при распространении

**Генерация контрольных сумм:**
```bash
# SHA256 для архива
sha256sum seo-entity-analyzer-1.0.0.tar.gz > checksums.txt

# MD5 для совместимости
md5sum seo-entity-analyzer-1.0.0.tar.gz >> checksums.txt
```

**Проверка целостности:**
```bash
# Проверка SHA256
sha256sum -c checksums.txt

# Вывод:
# seo-entity-analyzer-1.0.0.tar.gz: OK
```

**Docker автоматически проверяет:**
- Целостность слоев через SHA256
- Подпись образа (если настроено Docker Content Trust)

### 4.3. Требования к системе получателя

**Минимальные требования:**
- Docker Engine 20.10+ или Docker Desktop
- 2 GB RAM
- 1 GB свободного места на диске
- Поддерживаемые ОС:
  - Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)
  - Windows 10/11 с Docker Desktop
  - macOS 11+ с Docker Desktop

---

## 5. Управление API ключами (не лицензионными ключами ПО!)

### 5.1. Получение API ключей пользователем

Пользователь самостоятельно регистрируется и получает ключи:

#### 5.1.1. SerpAPI
1. Перейти на https://serpapi.com/
2. Зарегистрироваться (email + пароль)
3. Перейти в раздел "API Key"
4. Скопировать ключ вида: `abc123def456...`
5. **Бесплатно:** 100 запросов/месяц

#### 5.1.2. OpenRouter
1. Перейти на https://openrouter.ai/
2. Зарегистрироваться через GitHub / Google / Email
3. Перейти в раздел "Keys"
4. Создать новый ключ
5. Скопировать ключ вида: `sk-or-v1-abc123...`
6. **Бесплатно:** $5 trial кредита

### 5.2. Хранение API ключей

**Файл конфигурации (.env):**
```bash
# API ключи хранятся в переменных окружения
SERPAPI_KEY=abc123def456789...
OPENROUTER_API_KEY=sk-or-v1-abc123def456...
```

**Безопасность:**
- Файл `.env` НЕ включен в Git (`.gitignore`)
- Права доступа: `chmod 600 .env` (только владелец)
- Не передаётся вместе с Docker образом

**Альтернативный метод (для production):**
```bash
# Через переменные окружения при запуске
docker run -e SERPAPI_KEY=xxx -e OPENROUTER_API_KEY=yyy seo-entity-analyzer:1.0.0
```

### 5.3. Управление ключами в корпоративной среде

**Использование Secret Management систем:**

Пример с Docker Secrets:
```yaml
version: '3.8'
services:
  api:
    image: seo-entity-analyzer:1.0.0
    secrets:
      - serpapi_key
      - openrouter_key
    environment:
      SERPAPI_KEY_FILE: /run/secrets/serpapi_key
      OPENROUTER_KEY_FILE: /run/secrets/openrouter_key

secrets:
  serpapi_key:
    external: true
  openrouter_key:
    external: true
```

**Ротация ключей:**
1. Сгенерировать новый ключ в личном кабинете API
2. Обновить `.env` или секреты
3. Перезапустить контейнер: `docker-compose restart`
4. Удалить старый ключ в личном кабинете API

---

## 6. Отзыв и деактивация (для API ключей)

### 6.1. Отзыв API ключей

**Причины для отзыва:**
- Компрометация ключа
- Превышение лимитов использования
- Завершение trial периода

**Процесс:**
1. Войти в личный кабинет SerpAPI / OpenRouter
2. Перейти в раздел "API Keys"
3. Нажать "Revoke" или "Delete" напротив ключа
4. Подтвердить действие

**Последствия:**
- ПО продолжит работать в DEMO режиме
- Реальные API запросы будут возвращать ошибку 401 (Unauthorized)

### 6.2. Деактивация ПО

**Полная деактивация:**
```bash
# Остановка контейнера
docker-compose down

# Удаление образа
docker rmi seo-entity-analyzer:1.0.0

# Удаление данных
rm -rf logs/ reports/ .env
```

---

## 7. Аудит и мониторинг

### 7.1. Логирование использования API

**Логи сохраняются в:**
```
logs/app.log
```

**Пример записи:**
```
2026-01-21 10:15:30 | INFO | serp_service:get_results - 🔍 Fetching Yandex SERP: 'выкуп авто'
2026-01-21 10:15:32 | INFO | llm_service:extract_entities - 🤖 Analyzing text with DeepSeek V3.2
```

**Мониторинг расходов API:**
- SerpAPI Dashboard: https://serpapi.com/dashboard
- OpenRouter Dashboard: https://openrouter.ai/activity

### 7.2. Метрики использования

**Docker собирает метрики:**
```bash
# Статистика контейнера
docker stats seo-entity-analyzer

# Логи за период
docker logs --since 24h seo-entity-analyzer
```

---

## 8. Техническая поддержка

### 8.1. Проблемы с активацией

**Проблема:** ПО не запускается
**Решение:**
```bash
# Проверить логи
docker logs seo-entity-analyzer

# Проверить переменные окружения
docker exec seo-entity-analyzer env | grep -E "(DEMO_MODE|SERPAPI|OPENROUTER)"
```

**Проблема:** API ключи не работают
**Решение:**
1. Проверить формат ключа (нет лишних пробелов)
2. Проверить баланс в личном кабинете API
3. Проверить срок действия trial периода
4. Переключиться в DEMO режим для тестирования

### 8.2. Контактная информация

**Техническая поддержка:**
- Email: [support@example.com]
- Telegram: [@support_bot]
- Документация: [https://docs.example.com]

**Поддержка API сервисов:**
- SerpAPI: support@serpapi.com
- OpenRouter: support@openrouter.ai

---

## 9. Заключение

Программное обеспечение SEO Entity Analyzer использует гибридную модель работы:
- **DEMO режим** - полностью автономная работа без внешних зависимостей
- **PRODUCTION режим** - интеграция с внешними API сервисами

Данная архитектура обеспечивает:
- ✅ Простоту экспертной проверки (DEMO режим)
- ✅ Гибкость развертывания (Docker)
- ✅ Безопасность (API ключи управляются пользователем)
- ✅ Прозрачность (открытый исходный код, воспроизводимая сборка)

---

**Дата составления:** 21.01.2026
**Подпись ответственного лица:** _________________
