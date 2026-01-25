import os
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

    @abstractmethod
    async def list_tasks(self, page: int = 1, per_page: int = 20, status: Optional[str] = None) -> Dict[str, Any]:
        """Получить список задач с пагинацией"""
        pass

    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """Удалить задачу"""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory хранилище (для разработки)"""

    def __init__(self):
        self._storage: Dict[str, Dict] = {}
        logger.warning("⚠️ Using IN-MEMORY storage (not persistent!)")

    async def set_task(self, task_id: str, data: Dict[str, Any]) -> None:
        if task_id in self._storage:
            # Update existing
            self._storage[task_id].update(data)
            self._storage[task_id]["updated_at"] = datetime.utcnow().isoformat()
        else:
            # Create new
            self._storage[task_id] = {
                **data,
                "task_id": task_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._storage.get(task_id)

    async def exists(self, task_id: str) -> bool:
        return task_id in self._storage

    async def list_tasks(self, page: int = 1, per_page: int = 20, status: Optional[str] = None) -> Dict[str, Any]:
        """Получить список задач с пагинацией"""
        tasks = list(self._storage.values())

        # Фильтр по статусу
        if status:
            tasks = [t for t in tasks if t.get("status") == status]

        # Сортировка по дате создания (новые первые)
        tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Пагинация
        total = len(tasks)
        start = (page - 1) * per_page
        end = start + per_page
        items = tasks[start:end]

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": items
        }

    async def delete_task(self, task_id: str) -> bool:
        """Удалить задачу"""
        if task_id in self._storage:
            del self._storage[task_id]
            return True
        return False


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
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

        logger.info(f"🐘 PostgreSQL storage configured")
        self.engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def set_task(self, task_id: str, data: Dict[str, Any]) -> None:
        """Сохранить или обновить задачу"""
        from sqlalchemy import select, update
        from sqlalchemy.dialects.postgresql import insert
        from db.models import Task
        from datetime import datetime

        async with self.async_session() as session:
            try:
                # Преобразуем строковые даты в datetime объекты
                data_copy = data.copy()
                for field in ['created_at', 'updated_at']:
                    if field in data_copy and isinstance(data_copy[field], str):
                        data_copy[field] = datetime.fromisoformat(data_copy[field].replace('Z', '+00:00'))

                # Проверяем существование
                stmt = select(Task).where(Task.task_id == task_id)
                result = await session.execute(stmt)
                existing_task = result.scalar_one_or_none()

                if existing_task:
                    # Update existing - только непустые поля
                    # Удаляем None значения, чтобы не перезаписывать существующие данные
                    update_data = {k: v for k, v in data_copy.items() if v is not None}

                    if update_data:  # Обновляем только если есть что обновлять
                        stmt = (
                            update(Task)
                            .where(Task.task_id == task_id)
                            .values(**update_data)
                        )
                        await session.execute(stmt)
                else:
                    # Insert new
                    task = Task(task_id=task_id, **data_copy)
                    session.add(task)

                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Error saving task {task_id}: {e}")
                raise

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получить задачу по ID"""
        from sqlalchemy import select
        from db.models import Task

        async with self.async_session() as session:
            stmt = select(Task).where(Task.task_id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if task:
                task_dict = task.to_dict()

                # Восстановить region_name из region_id если отсутствует
                if task_dict.get('region_id') and not task_dict.get('region_name'):
                    from utils import region_manager
                    region = region_manager.get_by_id(task_dict['region_id'])
                    if region:
                        task_dict['region_name'] = region['title']
                        logger.debug(f"🔧 Auto-resolved region_name for task {task_id}: {region['title']}")

                return task_dict
            return None

    async def exists(self, task_id: str) -> bool:
        """Проверить существование задачи"""
        from sqlalchemy import select, exists
        from db.models import Task

        async with self.async_session() as session:
            stmt = select(exists().where(Task.task_id == task_id))
            result = await session.execute(stmt)
            return result.scalar()

    async def list_tasks(self, page: int = 1, per_page: int = 20, status: Optional[str] = None, created_by: Optional[str] = None) -> Dict[str, Any]:
        """Получить список задач с пагинацией"""
        from sqlalchemy import select, func
        from db.models import Task

        async with self.async_session() as session:
            # Base query
            stmt = select(Task)

            # Filter by status
            if status:
                stmt = stmt.where(Task.status == status)

            # Filter by created_by
            if created_by:
                stmt = stmt.where(Task.created_by == created_by)

            # Count total
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_result = await session.execute(count_stmt)
            total = total_result.scalar()

            # Sort by created_at desc
            stmt = stmt.order_by(Task.created_at.desc())

            # Pagination
            offset = (page - 1) * per_page
            stmt = stmt.offset(offset).limit(per_page)

            # Execute
            result = await session.execute(stmt)
            tasks = result.scalars().all()

            # Convert to dict and auto-resolve region_name if missing
            items = []
            for task in tasks:
                task_dict = task.to_dict()

                # Восстановить region_name из region_id если отсутствует
                if task_dict.get('region_id') and not task_dict.get('region_name'):
                    from utils import region_manager
                    region = region_manager.get_by_id(task_dict['region_id'])
                    if region:
                        task_dict['region_name'] = region['title']

                items.append(task_dict)

            return {
                "total": total,
                "page": page,
                "per_page": per_page,
                "items": items
            }

    async def delete_task(self, task_id: str) -> bool:
        """Удалить задачу"""
        from sqlalchemy import delete
        from db.models import Task

        async with self.async_session() as session:
            try:
                stmt = delete(Task).where(Task.task_id == task_id)
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount > 0
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Error deleting task {task_id}: {e}")
                return False


# === ФАБРИКА ХРАНИЛИЩ ===

def get_storage(backend: str = None) -> StorageBackend:
    """
    Получить хранилище по типу
    
    Args:
        backend: Тип хранилища ("memory", "redis", "postgres")
                 Если None, читается из STORAGE_BACKEND env variable
        
    Returns:
        Экземпляр хранилища
    """
    
    # Читаем из переменной окружения если не указано
    if backend is None:
        backend = os.getenv("STORAGE_BACKEND", "memory")
    
    logger.info(f"🔧 Initializing storage backend: {backend}")
    
    if backend == "memory":
        return InMemoryStorage()
    
    elif backend == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return RedisStorage(redis_url)
    
    elif backend == "postgres":
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL not configured")
        return PostgreSQLStorage(db_url)
    
    else:
        raise ValueError(f"Unknown storage backend: {backend}")


# Глобальный экземпляр (автоматически из .env)
storage = get_storage()