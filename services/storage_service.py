from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from datetime import datetime
from loguru import logger


class StorageBackend(ABC):
    """Абстрактный класс для хранилища"""
    
    @abstractmethod
    async def set_task(self, task_id: str, data: Dict[str, Any]) -> None:
        """Сохранить задачу"""
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получить задачу"""
        pass
    
    @abstractmethod
    async def exists(self, task_id: str) -> bool:
        """Проверить существование задачи"""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory хранилище (для разработки)"""
    
    def __init__(self):
        self._storage: Dict[str, Dict] = {}
        logger.warning("⚠️ Using IN-MEMORY storage (not persistent!)")
    
    async def set_task(self, task_id: str, data: Dict[str, Any]) -> None:
        self._storage[task_id] = {
            **data,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._storage.get(task_id)
    
    async def exists(self, task_id: str) -> bool:
        return task_id in self._storage


class RedisStorage(StorageBackend):
    """Redis хранилище (для production)"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        # TODO: Раскомментируй когда будешь использовать Redis
        # import aioredis
        # self.redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        logger.info(f"🔴 Redis storage configured: {redis_url}")
        raise NotImplementedError("Redis storage not implemented yet")
    
    async def set_task(self, task_id: str, data: Dict[str, Any]) -> None:
        # TODO: Реализовать
        # import json
        # await self.redis.set(f"task:{task_id}", json.dumps(data))
        pass
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        # TODO: Реализовать
        # import json
        # value = await self.redis.get(f"task:{task_id}")
        # return json.loads(value) if value else None
        pass
    
    async def exists(self, task_id: str) -> bool:
        # TODO: Реализовать
        # return await self.redis.exists(f"task:{task_id}")
        pass


class PostgreSQLStorage(StorageBackend):
    """PostgreSQL хранилище (для production)"""
    
    def __init__(self, db_url: str):
        # TODO: Раскомментируй когда будешь использовать PostgreSQL
        # from sqlalchemy.ext.asyncio import create_async_engine
        # self.engine = create_async_engine(db_url)
        logger.info(f"🐘 PostgreSQL storage configured: {db_url}")
        raise NotImplementedError("PostgreSQL storage not implemented yet")
    
    async def set_task(self, task_id: str, data: Dict[str, Any]) -> None:
        # TODO: Реализовать через SQLAlchemy
        pass
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        # TODO: Реализовать через SQLAlchemy
        pass
    
    async def exists(self, task_id: str) -> bool:
        # TODO: Реализовать через SQLAlchemy
        pass


# === ФАБРИКА ХРАНИЛИЩ ===

def get_storage(backend: str = "memory") -> StorageBackend:
    """
    Получить хранилище по типу
    
    Args:
        backend: Тип хранилища ("memory", "redis", "postgres")
        
    Returns:
        Экземпляр хранилища
    """
    
    if backend == "memory":
        return InMemoryStorage()
    
    elif backend == "redis":
        # import os
        # redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        # return RedisStorage(redis_url)
        raise NotImplementedError("Redis not configured yet")
    
    elif backend == "postgres":
        # import os
        # db_url = os.getenv("DATABASE_URL", "postgresql://...")
        # return PostgreSQLStorage(db_url)
        raise NotImplementedError("PostgreSQL not configured yet")
    
    else:
        raise ValueError(f"Unknown storage backend: {backend}")


# Глобальный экземпляр (пока in-memory)
storage = get_storage("memory")