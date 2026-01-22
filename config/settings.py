from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Настройки приложения"""

    # OpenRouter (DeepSeek V3.2)
    openrouter_api_key: str
    openrouter_model: str = "deepseek/deepseek-v3.2"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # SERP API
    serpapi_key: str

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    task_timeout_seconds: int = 300
    max_retries: int = 3

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Storage Backend
    storage_backend: str = "memory"
    database_url: Optional[str] = None
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None

    # Content limits
    min_content_length: int = 500
    max_content_length: int = 50000
    similarity_threshold: int = 85

    # Blacklist
    blacklist_domains: str = ""

    # SERP fetch multiplier - how many extra URLs to fetch to compensate for parsing failures
    serp_fetch_multiplier: int = 3

    @property
    def blacklist_domains_list(self) -> List[str]:
        """Преобразование строки blacklist в список"""
        if not self.blacklist_domains:
            return []
        return [d.strip() for d in self.blacklist_domains.split(",") if d.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Глобальный экземпляр настроек
settings = Settings()