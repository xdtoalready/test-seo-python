from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any


class AnalyzeRequest(BaseModel):
    """Запрос на анализ"""

    task_id: str = Field(
        ...,
        description="Уникальный ID задачи",
        min_length=3,
        max_length=100
    )

    task_name: Optional[str] = Field(
        default=None,
        description="Название задачи (для удобства пользователя)",
        max_length=200
    )

    keyword: str = Field(
        ...,
        description="Поисковый запрос",
        min_length=2,
        max_length=200
    )
    
    region_id: Optional[int] = Field(
        default=None,
        description="ID региона из yandex_region.json (для Яндекс и Google)"
    )
    
    region_name: Optional[str] = Field(
        default=None,
        description="Название региона (альтернатива region_id, будет найден автоматически)",
        max_length=100
    )
    
    target_url: Optional[str] = Field(
        default=None,
        description="URL своего сайта для сравнения (опционально)",
        max_length=500
    )

    created_by: Optional[str] = Field(
        default=None,
        description="Имя сотрудника, создавшего задачу",
        max_length=100
    )

    settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Дополнительные настройки"
    )
    
    @field_validator('settings')
    @classmethod
    def validate_settings(cls, v):
        """Валидация настроек"""
        if v is None:
            return {}
        
        # Установка дефолтных значений
        settings = {
            "depth": v.get("depth", 10),
            "engine": v.get("engine", "yandex"),
            "exclude_domains": v.get("exclude_domains", []),
        }
        
        # Валидация depth
        if not 1 <= settings["depth"] <= 100:
            raise ValueError("depth должен быть от 1 до 100")
        
        # Валидация engine
        if settings["engine"] not in ["yandex", "google"]:
            raise ValueError("engine должен быть 'yandex' или 'google'")
        
        return settings
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "test_123",
                "task_name": "Анализ выкупа авто в Москве",
                "keyword": "выкуп битых авто",
                "region_id": 213,
                "settings": {
                    "depth": 10,
                    "engine": "yandex"
                }
            }
        }


class RegionSearchRequest(BaseModel):
    """Поиск региона для автокомплита"""
    q: str = Field(..., min_length=2, max_length=100, description="Поисковый запрос")
    limit: int = Field(default=10, ge=1, le=50, description="Максимум результатов")