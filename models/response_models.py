from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """Ответ health check"""
    status: str = "ok"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalyzeResponse(BaseModel):
    """Ответ на запрос анализа"""
    task_id: str
    status: str = "queued"
    message: str = "Задача поставлена в очередь"
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "test_123",
                "status": "queued",
                "message": "Задача поставлена в очередь"
            }
        }


class TaskStatusResponse(BaseModel):
    """Статус выполнения задачи"""
    task_id: str
    status: str
    progress: Optional[int] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "test_123",
                "status": "processing",
                "progress": 50,
                "results": None,
                "error": None
            }
        }


class EntityResult(BaseModel):
    """Результат извлечения сущности"""
    entity_1: str
    relation: str
    entity_2: str
    context: Optional[str] = None


class AggregatedEntity(BaseModel):
    """Агрегированная сущность с частотой"""
    entity_1: str
    relation: str
    entity_2: str
    count: int
    urls: List[str]