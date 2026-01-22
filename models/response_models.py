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


class TaskListItem(BaseModel):
    """Элемент списка задач (краткая информация)"""
    task_id: str
    task_name: Optional[str] = None
    keyword: str
    region_name: Optional[str] = None
    engine: Optional[str] = None
    status: str
    progress: Optional[int] = None
    created_at: datetime
    total_entities: Optional[int] = None
    total_sources: Optional[int] = None


class TaskListResponse(BaseModel):
    """Ответ со списком задач"""
    total: int
    page: int
    per_page: int
    items: List[TaskListItem]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 42,
                "page": 1,
                "per_page": 20,
                "items": [
                    {
                        "task_id": "task-1769078061071",
                        "task_name": "Анализ займов Москва",
                        "keyword": "займ денег до зарплаты",
                        "region_name": "Москва",
                        "engine": "yandex",
                        "status": "completed",
                        "progress": 100,
                        "created_at": "2026-01-22T10:34:21Z",
                        "total_entities": 195,
                        "total_sources": 10
                    }
                ]
            }
        }


class TaskDetailResponse(BaseModel):
    """Детальная информация о задаче"""
    task_id: str
    task_name: Optional[str] = None
    keyword: str
    region_id: Optional[int] = None
    region_name: Optional[str] = None
    engine: Optional[str] = None
    depth: Optional[int] = None
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-1769078061071",
                "task_name": "Анализ займов Москва",
                "keyword": "займ денег до зарплаты",
                "region_id": 213,
                "region_name": "Москва",
                "engine": "yandex",
                "depth": 10,
                "status": "completed",
                "progress": 100,
                "message": "Анализ завершен",
                "created_at": "2026-01-22T10:34:21Z",
                "updated_at": "2026-01-22T10:35:56Z",
                "results": {
                    "total_entities": 195,
                    "total_sources": 10,
                    "universal_entities": 1,
                    "common_entities": 1,
                    "rare_entities": 195,
                    "excel_file": "task-1769078061071.xlsx"
                },
                "error": None
            }
        }