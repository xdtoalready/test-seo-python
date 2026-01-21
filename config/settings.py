from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Настройки приложения"""

    # Demo Mode (для экспертной проверки без реальных API)
    demo_mode: bool = False

    # OpenRouter (DeepSeek V3.2)
    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-v3.2"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # SERP API
    serpapi_key: str = ""

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    task_timeout_seconds: int = 300
    max_retries: int = 3
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Content limits
    min_content_length: int = 500
    max_content_length: int = 50000
    similarity_threshold: int = 85
    
    # Blacklist
    blacklist_domains: str = ""
    
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