# Пакет для экспертной проверки
# SEO Entity Analyzer v1.0.0

## Содержимое архива
```
expert_package_seo_analyzer_v1.0.0.zip
├── docker_image/
│   └── seo-entity-analyzer_1.0.0.tar    # Docker образ (можно загрузить через docker load)
├── config/
│   ├── docker-compose.yml                # Конфигурация для запуска
│   └── .env.demo                         # Готовые настройки для DEMO режима
├── documentation/
│   ├── 01_storage_and_compilation.pdf
│   ├── 02_licensing_and_distribution.pdf
│   ├── 03_installation_guide.pdf
│   ├── 04_functional_characteristics.pdf
│   ├── 05_lifecycle_and_support.pdf
│   └── 06_operation_and_testing_guide.pdf
└── QUICK_START.pdf                       # Этот файл
```

## Быстрый старт (5 минут)

### Шаг 1: Загрузить Docker образ
```bash
cd docker_image
docker load -i seo-entity-analyzer_1.0.0.tar
```

### Шаг 2: Запустить контейнер
```bash
cd ../config
cp .env.demo .env
docker-compose up -d
```

### Шаг 3: Проверить работу

Откройте браузер: http://localhost:8000/api/v1/docs

### Шаг 4: Выполнить тестовый запрос

В интерфейсе Swagger UI:
1. Откройте POST /api/v1/analyze
2. Нажмите "Try it out"
3. Используйте тестовые данные:
```json
{
  "task_id": "test_001",
  "keyword": "выкуп битых автомобилей",
  "region": "Москва",
  "settings": {
    "depth": 10
  }
}
```
4. Нажмите "Execute"
5. Через 5-10 секунд проверьте результат через GET /api/v1/status/test_001

## Важная информация

- **Режим работы:** DEMO (предзаписанные данные)
- **API ключи:** НЕ требуются
- **Интернет:** НЕ требуется (кроме загрузки образа)
- **Время тестирования:** ~30 минут
- **Системные требования:** 
  - 4 GB RAM
  - 2 CPU cores
  - 5 GB свободного места на диске

## Техническая поддержка для экспертов

**Контактное лицо:** [ИМЯ, ДОЛЖНОСТЬ]
**Email:** [EMAIL]
**Телефон:** [ТЕЛЕФОН] (рабочие дни 10:00-18:00 МСК)

**Срок реагирования:** В течение 2 часов в рабочее время

## Контрольные суммы

SHA256 (seo-entity-analyzer_1.0.0.tar): [HASH]
MD5 (expert_package.zip): [HASH]