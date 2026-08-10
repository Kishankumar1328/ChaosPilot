import logging
from sqlalchemy import text
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

# Base engine initialization
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_mysql_database_if_not_exists():
    """
    Connects to MySQL server using root credentials and creates the target database if it doesn't exist.
    """
    if "mysql" in settings.DATABASE_URL:
        try:
            # Base server URL without database name
            server_url = f"mysql+aiomysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
            root_engine = create_async_engine(server_url, isolation_level="AUTOCOMMIT")
            async with root_engine.connect() as conn:
                await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DB}"))
            await root_engine.dispose()
            logger.info(f"MySQL database '{settings.MYSQL_DB}' verified/created successfully.")
        except Exception as e:
            logger.warning(f"Could not auto-create MySQL database '{settings.MYSQL_DB}': {e}")

async def init_db():
    global engine, async_session_maker
    try:
        await create_mysql_database_if_not_exists()
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database initialized successfully with MySQL.")
    except Exception as e:
        logger.warning(f"MySQL initialization error: {e}. Switching to SQLite fallback database.")
        engine = create_async_engine(settings.FALLBACK_DATABASE_URL, echo=False, future=True)
        async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("SQLite fallback database initialized successfully.")

async def get_session():
    async with async_session_maker() as session:
        yield session
