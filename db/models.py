"""SQLAlchemy models"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from db.database import Base


class Task(Base):
    """Модель задачи анализа"""

    __tablename__ = "tasks"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Task identification
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    task_name = Column(String(200), nullable=True)

    # Search parameters
    keyword = Column(String(200), nullable=False)
    region_id = Column(Integer, nullable=True)
    region_name = Column(String(100), nullable=True)
    engine = Column(String(20), nullable=True)  # "yandex" or "google"
    depth = Column(Integer, nullable=True)

    # Task status
    status = Column(String(50), nullable=False, default="queued", index=True)
    progress = Column(Integer, default=0)
    message = Column(String(500), nullable=True)

    # Results
    excel_file = Column(String(500), nullable=True)
    results = Column(JSON, nullable=True)  # Stores statistics and metadata

    # Error handling
    error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Future: user tracking for Laravel integration
    created_by = Column(String(100), nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_tasks_created_at_desc', created_at.desc()),
        Index('idx_tasks_status', status),
        Index('idx_tasks_keyword', keyword),
    )

    def __repr__(self):
        return f"<Task(task_id={self.task_id}, status={self.status}, keyword={self.keyword})>"

    def to_dict(self):
        """Преобразование модели в словарь"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "keyword": self.keyword,
            "region_id": self.region_id,
            "region_name": self.region_name,
            "engine": self.engine,
            "depth": self.depth,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "excel_file": self.excel_file,
            "results": self.results,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }
