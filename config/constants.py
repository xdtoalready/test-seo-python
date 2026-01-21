# Версия API
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Поддерживаемые поисковые системы
SUPPORTED_SEARCH_ENGINES = ["yandex", "google"]

# Региональные коды для Яндекса
# YANDEX_REGIONS = {
#     "Москва": 213,
#     "Санкт-Петербург": 2,
#     "Екатеринбург": 54,
#     "Новосибирск": 65,
#     "Нижний Новгород": 47,
#     "Казань": 43,
#     "Челябинск": 56,
#     "Омск": 66,
#     "Самара": 51,
#     "Ростов-на-Дону": 39,
#     "Уфа": 172,
#     "Красноярск": 62,
#     "Воронеж": 193,
#     "Пермь": 50,
#     "Волгоград": 38,
# }

# Лимиты контента
DEFAULT_SERP_DEPTH = 10
MAX_SERP_DEPTH = 100
MIN_PAGE_CONTENT_LENGTH = 500
MAX_PAGE_CONTENT_LENGTH = 50000

# Таймауты (в секундах)
HTTP_REQUEST_TIMEOUT = 30
OPENROUTER_TIMEOUT = 120

# Параметры ИИ
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 4000

# Параметры агрегации
DEFAULT_SIMILARITY_THRESHOLD = 85
MIN_SIMILARITY_THRESHOLD = 70
MAX_SIMILARITY_THRESHOLD = 95

# Статусы задач
TASK_STATUS_QUEUED = "queued"
TASK_STATUS_PROCESSING = "processing"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"

# User Agent для парсинга
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# === OPENROUTER / LLM SETTINGS ===
OPENROUTER_TIMEOUT = 120  # 2 минуты на запрос