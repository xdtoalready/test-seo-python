# 🚀 Production Deployment Guide

## Обновление .env файла на сервере

**Путь:** `/home/web/serp-search-backend/prod/.env`

### Что изменить:

1. **Заменить STORAGE_BACKEND:**
```bash
# Было:
STORAGE_BACKEND=redis

# Стало:
STORAGE_BACKEND=postgres
```

2. **Добавить/обновить DATABASE_URL:**
```bash
# Раскомментировать и обновить:
DATABASE_URL=postgresql+asyncpg://seo_user:SuperStr0ng_Pa$$w0rd_2026@postgres:5432/seo_analyzer
POSTGRES_PASSWORD=SuperStr0ng_Pa$$w0rd_2026
```

3. **Убрать/закомментировать Redis (пока не используется):**
```bash
# Закомментировать:
# REDIS_URL=redis://redis:6379/0
# REDIS_PASSWORD=your_strong_redis_password_here
```

4. **Добавить новую настройку SERP_FETCH_MULTIPLIER:**
```bash
# Добавить в секцию SERP FETCHING:
SERP_FETCH_MULTIPLIER=3
```

---

## Полный обновленный .env для production

```bash
# === PRODUCTION CONFIGURATION ===

# === OPENROUTER API ===
OPENROUTER_API_KEY=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
OPENROUTER_MODEL=deepseek/deepseek-v3.2
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# === SERP API ===
SERPAPI_KEY=069bdbc589389aa4f1d9c7408047b349f80bcddcd0adcf99980f86453a345be0

# === APPLICATION ===
ENVIRONMENT=production
LOG_LEVEL=INFO
TASK_TIMEOUT_SECONDS=300
MAX_RETRIES=3

# === STORAGE BACKEND ===
STORAGE_BACKEND=postgres

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://seo_user:SuperStr0ng_Pa$$w0rd_2026@postgres:5432/seo_analyzer
POSTGRES_PASSWORD=SuperStr0ng_Pa$$w0rd_2026

# Redis (future for caching)
# REDIS_URL=redis://redis:6379/0
# REDIS_PASSWORD=your_strong_redis_password_here

# === CONTENT LIMITS ===
MIN_CONTENT_LENGTH=500
MAX_CONTENT_LENGTH=50000
SIMILARITY_THRESHOLD=85

# === BLACKLIST DOMAINS ===
BLACKLIST_DOMAINS=avito.ru,drom.ru,auto.ru,youla.ru,irr.ru,olx.ru,farpost.ru,yandex.ru,maps.yandex.ru,uslugi.yandex.ru

# === SERP FETCHING ===
SERP_FETCH_MULTIPLIER=3

# === API ===
API_HOST=0.0.0.0
API_PORT=8000
```

**ВАЖНО:** Замените `SuperStr0ng_Pa$$w0rd_2026` на свой надежный пароль!

---

## Обновление GitLab CI

Файл `.gitlab-ci.yml` - обновить команду остановки контейнеров:

**Было:**
```yaml
- docker stop seo-analyzer-api seo-analyzer-redis || true
- docker rm seo-analyzer-api seo-analyzer-redis || true
```

**Стало:**
```yaml
- docker stop seo-analyzer-api seo-analyzer-postgres || true
- docker rm seo-analyzer-api seo-analyzer-postgres || true
```

---

## Пошаговая инструкция деплоя

### Вариант А: Автоматический (через GitLab)

1. **На локальной машине:**
```bash
git add .
git commit -m "Add PostgreSQL storage for production"
git push origin main
```

2. **GitLab CI автоматически:**
   - Выполнит pull на сервере
   - Остановит старые контейнеры
   - Пересоберет с новым docker-compose.prod.yml
   - Запустит PostgreSQL + API

3. **Проверить логи:**
```bash
ssh your-server
cd /home/web/serp-search-backend/prod
docker-compose -p seo-analyzer-prod logs -f api
```

Должны увидеть:
```
✅ Database tables created
✅ Database initialized successfully
🚀 Starting SEO Entity Analyzer API
```

### Вариант Б: Ручной деплой (безопаснее для первого раза)

1. **SSH на сервер:**
```bash
ssh your-server
cd /home/web/serp-search-backend/prod
```

2. **Обновить код:**
```bash
sudo -H -u web git pull
```

3. **Обновить .env файл:**
```bash
nano .env
# Внести изменения согласно инструкции выше
# Сохранить: Ctrl+O, Enter, Ctrl+X
```

4. **Остановить старые контейнеры:**
```bash
docker stop seo-analyzer-api seo-analyzer-postgres || true
docker rm seo-analyzer-api seo-analyzer-postgres || true
```

5. **Запустить с новым compose:**
```bash
/usr/bin/docker compose -p seo-analyzer-prod -f docker-compose.prod.yml up --build -d
```

6. **Проверить статус:**
```bash
docker ps
# Должны быть запущены: seo-analyzer-api, seo-analyzer-postgres

docker-compose -p seo-analyzer-prod logs -f api
# Ctrl+C для выхода
```

7. **Проверить что API работает:**
```bash
curl http://localhost:8001/health
# {"status":"ok","version":"1.0.0","timestamp":"..."}

curl http://localhost:8001/api/v1/tasks
# {"total":0,"page":1,"per_page":20,"items":[]}
```

---

## Проверка работоспособности

### 1. Проверить что контейнеры запущены:
```bash
docker ps | grep seo-analyzer
```

Должны быть:
- `seo-analyzer-api` (healthy)
- `seo-analyzer-postgres` (healthy)

### 2. Проверить логи PostgreSQL:
```bash
docker logs seo-analyzer-postgres | tail -20
```

Должно быть:
```
database system is ready to accept connections
```

### 3. Проверить логи API:
```bash
docker logs seo-analyzer-api | tail -50
```

Должно быть:
```
🐘 Configuring PostgreSQL: postgres:5432/seo_analyzer
🔧 Creating database tables...
✅ Database tables created
✅ Database initialized successfully
🚀 Starting SEO Entity Analyzer API
Storage Backend: postgres
```

### 4. Создать тестовую задачу:
```bash
curl -X POST "http://localhost:8001/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "prod-test-001",
    "task_name": "Production Test",
    "keyword": "тест production",
    "settings": {"depth": 10, "engine": "yandex"}
  }'
```

### 5. Проверить что задача сохранилась:
```bash
curl "http://localhost:8001/api/v1/tasks" | jq
```

Должна вернуться задача `prod-test-001`.

### 6. Перезапустить контейнеры и убедиться что данные сохранились:
```bash
docker-compose -p seo-analyzer-prod restart
sleep 5
curl "http://localhost:8001/api/v1/tasks" | jq
```

Задача должна все еще быть в базе! ✅

---

## Backup базы данных

### Создать backup:
```bash
docker exec seo-analyzer-postgres pg_dump -U seo_user seo_analyzer > \
  /home/web/serp-search-backend/backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Настроить автоматический backup (cron):
```bash
crontab -e

# Добавить строку (backup каждый день в 3:00 AM):
0 3 * * * docker exec seo-analyzer-postgres pg_dump -U seo_user seo_analyzer > /home/web/serp-search-backend/backups/backup_$(date +\%Y\%m\%d).sql
```

### Восстановить из backup:
```bash
cat /path/to/backup.sql | docker exec -i seo-analyzer-postgres psql -U seo_user seo_analyzer
```

---

## Troubleshooting

### Проблема: API не запускается
```bash
# Проверить логи
docker logs seo-analyzer-api

# Проверить .env
cat .env | grep STORAGE_BACKEND
cat .env | grep DATABASE_URL
```

### Проблема: PostgreSQL не стартует
```bash
# Проверить логи
docker logs seo-analyzer-postgres

# Проверить volume
docker volume ls | grep postgres

# В крайнем случае пересоздать (УДАЛИТ ДАННЫЕ!)
docker-compose -p seo-analyzer-prod down -v
docker-compose -p seo-analyzer-prod up -d
```

### Проблема: "Database connection failed"
```bash
# Проверить что PostgreSQL доступен
docker exec seo-analyzer-api ping postgres -c 3

# Проверить credentials
docker exec seo-analyzer-postgres psql -U seo_user -d seo_analyzer -c "SELECT 1;"
```

---

## Порты

- **API:** `8001` (внешний) → `8000` (внутри контейнера)
- **PostgreSQL:** `5433` (внешний) → `5432` (внутри контейнера)

Если нужен прямой доступ к PostgreSQL извне:
```bash
psql -h your-server -p 5433 -U seo_user -d seo_analyzer
```

---

## Мониторинг

### Посмотреть использование ресурсов:
```bash
docker stats seo-analyzer-api seo-analyzer-postgres
```

### Посмотреть размер базы данных:
```bash
docker exec seo-analyzer-postgres psql -U seo_user -d seo_analyzer -c "
  SELECT pg_size_pretty(pg_database_size('seo_analyzer'));"
```

### Посмотреть количество задач в БД:
```bash
docker exec seo-analyzer-postgres psql -U seo_user -d seo_analyzer -c "
  SELECT status, COUNT(*) FROM tasks GROUP BY status;"
```

---

## Откат на старую версию

Если что-то пошло не так:

```bash
cd /home/web/serp-search-backend/prod

# Откатить git
git log --oneline -5
git reset --hard <старый_commit>

# Пересобрать
docker-compose -p seo-analyzer-prod down
docker-compose -p seo-analyzer-prod up --build -d
```

**ВАЖНО:** Volumes (данные) сохранятся!
