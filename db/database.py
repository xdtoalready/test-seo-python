"""Database configuration and session management"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger
from config import settings

# SQLAlchemy Base
Base = declarative_base()

# Engine (создается только если DATABASE_URL настроен)
engine = None
async_session = None

if settings.database_url:
    logger.info(f"🐘 Configuring PostgreSQL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'localhost'}")

    engine = create_async_engine(
        settings.database_url,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,
        max_overflow=10,
    )

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
else:
    logger.warning("⚠️ DATABASE_URL not configured, PostgreSQL storage will not be available")


async def get_db() -> AsyncSession:
    """
    Dependency для получения сессии БД

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    if not async_session:
        raise RuntimeError("Database not configured. Set DATABASE_URL in .env")

    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Инициализация БД (создание таблиц)

    Note: В продакшене лучше использовать Alembic migrations
    """
    if not engine:
        logger.warning("⚠️ Cannot init DB: engine not configured")
        return

    from db.models import Task  # Import here to avoid circular dependency

    logger.info("🔧 Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created")
