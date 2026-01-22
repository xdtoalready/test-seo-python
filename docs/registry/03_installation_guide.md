# Программное обеспечение «SEO Entity Analyzer»
**Правообладатель:** [НАЗВАНИЕ КОМПАНИИ], ИНН [ИНН], ОГРН [ОГРН]
**Документ:** Инструкция по установке экземпляра программного обеспечения, предоставленного для проведения экспертной проверки

---

## Содержание

1. [Системные требования](#1-системные-требования)
2. [Установка Docker](#2-установка-docker)
3. [Получение программного обеспечения](#3-получение-программного-обеспечения)
4. [Установка в DEMO режиме](#4-установка-в-demo-режиме-рекомендуется-для-экспертизы)
5. [Установка в PRODUCTION режиме](#5-установка-в-production-режиме)
6. [Проверка работоспособности](#6-проверка-работоспособности)
7. [Решение проблем](#7-решение-проблем)

---

## 1. Системные требования

### 1.1. Минимальные требования

| Компонент | Требование |
|-----------|-----------|
| **Процессор** | 2 ядра (x86_64 / ARM64) |
| **Оперативная память** | 2 GB RAM |
| **Дисковое пространство** | 2 GB свободного места |
| **Сеть** | Доступ к интернету (для скачивания образа) |

### 1.2. Поддерживаемые операционные системы

#### Linux:
- Ubuntu 20.04 LTS и выше
- Debian 11 (Bullseye) и выше
- RHEL 8+ / CentOS 8+ / Rocky Linux 8+
- Fedora 35+

#### Windows:
- Windows 10 Pro/Enterprise (версия 1903 и выше)
- Windows 11 Pro/Enterprise
- Windows Server 2019/2022

#### macOS:
- macOS 11 (Big Sur) и выше
- Поддержка Intel и Apple Silicon (M1/M2)

#### ПО является кроссплатформенным благодаря использованию технологии контейнеризации. Поддерживаются:

- Российские ОС: Astra Linux (релиз «Воронеж»/«Орел»), РЕД ОС, Альт Линукс.
- Прочие ОС: Любые дистрибутивы на базе ядра Linux с установленным Docker.

### 1.3. Необходимое программное обеспечение

**Обязательно:**
- Docker Engine 20.10+ ИЛИ Docker Desktop
- Docker Compose 1.29+ (обычно входит в Docker Desktop)

**Опционально (для production режима):**
- API ключи SerpAPI и OpenRouter (см. раздел 5)

---

## 2. Установка Docker

### 2.1. Поддерживаемые операционные системы

**ПО протестировано и гарантируется корректная работа на следующих операционных системах:**

**Linux (рекомендуется):**
- Ubuntu 20.04 / 22.04 / 24.04
- Debian 11 / 12
- **Astra Linux SE 1.7 / 1.8** ✅ (российская ОС)
- **РЕД ОС 7.x / 8.x** ✅ (российская ОС)
- CentOS 7 / 8
- Rocky Linux 8 / 9
- Любой дистрибутив Linux с поддержкой Docker 20.10+

**Windows:**
- Windows 10 / 11 (с Docker Desktop)
- Windows Server 2019 / 2022

**macOS:**
- macOS 11 Big Sur и выше

**Важно для российских ОС:**
ПО работает в Docker контейнере, что обеспечивает полную совместимость с российскими операционными системами (Astra Linux, РЕД ОС) при условии установленной среды контейнеризации Docker версии 20.10 или выше.

---

### 2.2. Установка Docker на Windows

1. Скачать Docker Desktop для Windows:
   https://www.docker.com/products/docker-desktop/

2. Запустить установщик `Docker Desktop Installer.exe`

3. Следовать инструкциям установщика:
   - Принять лицензионное соглашение
   - Выбрать конфигурацию (рекомендуется WSL 2)
   - Дождаться завершения установки

4. Перезагрузить компьютер

5. Запустить Docker Desktop

6. Проверка:
   ```powershell
   # Открыть PowerShell или cmd
   docker --version
   docker compose version
   ```

### 2.3. Установка Docker на macOS

1. Скачать Docker Desktop для macOS:
   https://www.docker.com/products/docker-desktop/

2. Открыть скачанный `.dmg` файл

3. Перетащить Docker в папку Applications

4. Запустить Docker из Applications

5. Предоставить необходимые разрешения (при запросе)

6. Проверка:
   ```bash
   # Открыть Terminal
   docker --version
   docker compose version
   ```

---

## 3. Получение программного обеспечения

Дистрибутив ПО предоставляется в виде единого архива, содержащего объектный код (Docker-образ в формате .tar) и конфигурационные файлы. Ссылка на загрузку предоставляется в личном кабинете на сайте правообладателя или в сопроводительном письме для экспертной проверки.

### 3.1. Метод 1: Через Docker Registry (рекомендуется)

```bash
# Скачать последнюю версию образа
docker pull registry.example.com/seo-entity-analyzer:1.0.0

# ИЛИ скачать с альтернативного источника
docker pull seo-entity-analyzer:1.0.0
```

### 3.2. Метод 2: Из архива (офлайн установка)

```bash
# Если предоставлен .tar файл образа
docker load -i seo-entity-analyzer-1.0.0.tar

# Проверить загруженные образы
docker images | grep seo-entity-analyzer
```

### 3.3. Метод 3: Сборка из исходного кода

```bash
# Если предоставлен архив с исходным кодом
tar -xzf seo-entity-analyzer-1.0.0-src.tar.gz
cd seo-entity-analyzer-1.0.0

# Собрать Docker образ
docker build -t seo-entity-analyzer:1.0.0 .

# Процесс займёт 3-5 минут
```

### 3.4. Проверка полученного образа

```bash
# Просмотр информации об образе
docker inspect seo-entity-analyzer:1.0.0

# Проверка размера
docker images seo-entity-analyzer:1.0.0

# Ожидаемый размер: ~500 MB
```

### 3.5. Установка Docker на российских ОС

#### Для Astra Linux SE:
```bash
# Установка Docker из официального репозитория Astra Linux
sudo apt update
sudo apt install docker.io
sudo systemctl enable docker
sudo systemctl start docker

# Проверка
docker --version
```

#### Для РЕД ОС:
```bash
# Установка Docker из репозитория РЕД ОС
sudo dnf install docker-ce docker-ce-cli containerd.io
sudo systemctl enable docker
sudo systemctl start docker

# Проверка
docker --version
```

**Примечание:** ПО тестировалось на Astra Linux SE 1.7 и РЕД ОС 7.3. Полная совместимость подтверждена.

---

## 4. Установка для экспертной проверки (DEMO режим)

### 4.1. Преимущества DEMO режима

- ✅ Не требует API ключей
- ✅ Работает полностью автономно
- ✅ Демонстрирует все функции ПО
- ✅ Использует предзаписанные mock данные
- ✅ Бесплатно
**Важно для экспертов:** DEMO режим использует предзаписанные тестовые данные и не требует регистрации в внешних сервисах или API ключей. Все функции ПО доступны для проверки.

### 4.2. Пошаговая установка

**Шаг 1: Создать рабочую директорию**
```bash
mkdir seo-analyzer-demo
cd seo-analyzer-demo
```

**Шаг 2: Создать файл конфигурации**
```bash
# Создать файл .env с demo настройками
cat > .env << 'EOF'
# DEMO MODE Configuration
DEMO_MODE=true

# API Keys (not required in demo mode)
OPENROUTER_API_KEY=
SERPAPI_KEY=

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Storage
STORAGE_BACKEND=memory

# Content Limits
MIN_CONTENT_LENGTH=500
MAX_CONTENT_LENGTH=50000
SIMILARITY_THRESHOLD=85
BLACKLIST_DOMAINS=avito.ru,drom.ru,auto.ru
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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
EOF
```

**Шаг 4: Запустить контейнер**
```bash
# Запуск в фоновом режиме
docker compose up -d

# Просмотр логов запуска
docker compose logs -f

# Ожидаемый вывод:
# 🎭 DEMO MODE: Using mock SERP data
# 🎭 DEMO MODE: Using mock LLM data
# 🎭 DEMO MODE: Using mock parser data
# 🚀 Starting SEO Entity Analyzer API
# Application startup complete

# Остановить просмотр логов: Ctrl+C
```

**Шаг 5: Проверить запуск**
```bash
# Проверить статус контейнера
docker ps | grep seo-analyzer

# Должен быть статус "Up"
```

### 4.3. Доступ к веб-интерфейсу

Откройте в браузере:
```
http://localhost:8000/api/v1/docs
```

Вы увидите интерактивную документацию API (Swagger UI).

---

## 5. Установка в PRODUCTION режиме

### 5.1. Получение API ключей

#### 5.1.1. Получение ключа SerpAPI

1. Перейти на https://serpapi.com/
2. Нажать "Sign Up" (Зарегистрироваться)
3. Заполнить форму регистрации (email, пароль)
4. Подтвердить email
5. В личном кабинете перейти в "API Key"
6. Скопировать ключ (формат: `abc123def456...`)

**Бесплатный план:** 100 запросов/месяц

#### 5.1.2. Получение ключа OpenRouter

1. Перейти на https://openrouter.ai/
2. Нажать "Sign In" и выбрать способ регистрации (GitHub / Google / Email)
3. В личном кабинете перейти в "Keys"
4. Нажать "Create Key"
5. Скопировать ключ (формат: `sk-or-v1-abc123def456...`)

**Бесплатный trial:** $5 кредита

### 5.2. Установка в production режиме

**Шаг 1: Создать рабочую директорию**
```bash
mkdir seo-analyzer-production
cd seo-analyzer-production
```

**Шаг 2: Создать файл конфигурации**
```bash
cat > .env << 'EOF'
# PRODUCTION MODE Configuration
DEMO_MODE=false

# API Keys (обязательно заполнить!)
OPENROUTER_API_KEY=sk-or-v1-ВАШ_КЛЮЧ_ЗДЕСЬ
SERPAPI_KEY=ВАШ_КЛЮЧ_ЗДЕСЬ

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Storage
STORAGE_BACKEND=memory

# Content Limits
MIN_CONTENT_LENGTH=500
MAX_CONTENT_LENGTH=50000
SIMILARITY_THRESHOLD=85
BLACKLIST_DOMAINS=avito.ru,drom.ru,auto.ru
EOF

# ВАЖНО: Заменить "ВАШ_КЛЮЧ_ЗДЕСЬ" на реальные ключи!
```

**Шаг 3: Создать docker-compose.yml** (аналогично demo режиму)

**Шаг 4: Запустить контейнер**
```bash
docker compose up -d
docker compose logs -f
```

Ожидаемый вывод:
```
✅ SERPAPI_KEY configured
✅ OPENROUTER_API_KEY configured
🚀 Starting in production mode
```

---

## 6. Проверка работоспособности

### 6.1. Проверка доступности API

```bash
# Health check
curl http://localhost:8000/health

# Ожидаемый ответ:
# {
#   "status": "ok",
#   "version": "1.0.0",
#   "timestamp": "2026-01-21T10:00:00"
# }
```

### 6.2. Тестовый запрос (DEMO режим)

```bash
# Отправить запрос на анализ
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-001",
    "keyword": "выкуп битых автомобилей",
    "region_id": 213,
    "settings": {
      "depth": 10,
      "engine": "yandex"
    }
  }'

# Ответ:
# {
#   "task_id": "test-001",
#   "status": "queued",
#   "message": "Задача 'test-001' поставлена в очередь"
# }
```

**Проверка статуса задачи:**
```bash
# Подождать 10-15 секунд, затем:
curl http://localhost:8000/api/v1/status/test-001

# Ответ должен показать progress и результаты
```

**Скачивание отчета:**
```bash
# Когда status = "completed"
curl -O http://localhost:8000/api/v1/download/test-001

# Откроется файл test-001.xlsx
```

### 6.3. Проверка через веб-интерфейс

1. Открыть http://localhost:8000/api/v1/docs
2. Найти endpoint `/api/v1/analyze`
3. Нажать "Try it out"
4. Ввести параметры:
   ```json
   {
     "task_id": "web-test-001",
     "keyword": "выкуп битых автомобилей",
     "region_id": 213,
     "settings": {
       "depth": 10,
       "engine": "yandex"
     }
   }
   ```
5. Нажать "Execute"
6. Проверить ответ

---

## 7. Решение проблем

### 7.1. Контейнер не запускается

**Проблема:**
```bash
docker compose up
# Error: Cannot connect to Docker daemon
```

**Решение:**
```bash
# Проверить что Docker запущен
sudo systemctl status docker  # Linux
# ИЛИ проверить Docker Desktop (Windows/macOS)

# Запустить Docker
sudo systemctl start docker  # Linux
```

### 7.2. Порт 8000 уже занят

**Проблема:**
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Решение 1:** Остановить процесс на порту 8000
```bash
# Linux/macOS
sudo lsof -i :8000
sudo kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Решение 2:** Изменить порт в docker-compose.yml
```yaml
ports:
  - "8001:8000"  # Внешний порт 8001
```

### 7.3. Ошибка "Cannot find image"

**Проблема:**
```
Error: Unable to find image 'seo-entity-analyzer:1.0.0' locally
```

**Решение:**
```bash
# Проверить доступные образы
docker images

# Если образа нет, загрузить его (см. раздел 3)
docker pull seo-entity-analyzer:1.0.0
# ИЛИ
docker load -i seo-entity-analyzer-1.0.0.tar
```

### 7.4. Ошибка API ключей (production режим)

**Проблема в логах:**
```
❌ OpenRouter API error: 401 Unauthorized
```

**Решение:**
1. Проверить что ключи скопированы правильно (без пробелов)
2. Проверить срок действия trial периода
3. Проверить баланс в личном кабинете
4. Переключиться на DEMO режим для тестирования:
   ```bash
   # В файле .env изменить:
   DEMO_MODE=true

   # Перезапустить контейнер
   docker compose restart
   ```

### 7.5. Контейнер останавливается сразу после запуска

**Проверка логов:**
```bash
# Просмотр логов
docker logs seo-analyzer

# Если контейнер уже остановился
docker logs --tail 50 seo-analyzer
```

**Частые причины:**
- Ошибка в .env файле (неправильный формат)
- Недостаточно памяти (требуется минимум 2GB)
- Конфликт портов

### 7.6. Получение поддержки

**Логи для отправки в поддержку:**
```bash
# Собрать диагностическую информацию
docker ps -a > docker-status.txt
docker logs seo-analyzer > application-logs.txt
docker inspect seo-analyzer > container-info.txt

# Отправить файлы в техническую поддержку
```

---

## 8. Управление установкой

### 8.1. Остановка ПО
```bash
# Остановить контейнер
docker compose stop

# Остановить и удалить контейнер
docker compose down
```

### 8.2. Обновление ПО
```bash
# Остановить текущую версию
docker compose down

# Скачать новую версию
docker pull seo-entity-analyzer:1.1.0

# Обновить тег в docker-compose.yml:
# image: seo-entity-analyzer:1.1.0

# Запустить новую версию
docker compose up -d
```

### 8.3. Полное удаление
```bash
# Остановить и удалить контейнер
docker compose down

# Удалить образ
docker rmi seo-entity-analyzer:1.0.0

# Удалить данные (опционально)
rm -rf logs/ reports/ .env
```

---

## 9. Контрольный чек-лист для экспертов

- [ ] Docker установлен и запущен (`docker --version`)
- [ ] Образ загружен (`docker images | grep seo-entity-analyzer`)
- [ ] Файл .env создан с DEMO_MODE=true
- [ ] Контейнер запущен (`docker ps | grep seo-analyzer`)
- [ ] API доступен (http://localhost:8000/health)
- [ ] Swagger UI открывается (http://localhost:8000/api/v1/docs)
- [ ] Тестовый запрос выполнен успешно
- [ ] Отчет Excel сгенерирован и скачан

---

**Техническая поддержка:**
- Email: support@example.com
- Документация: См. README.md в корне проекта

**Дата составления:** 21.01.2026
