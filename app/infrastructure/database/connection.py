"""
Подключение к PostgreSQL
"""

import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()


class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.async_session_maker = None

    async def initialize(self):
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            pool_pre_ping=True,
        )

        self.async_session_maker = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ PostgreSQL initialized")

    async def get_session(self):
        """Получение сессии"""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
                print("=== COMMIT SUCCESSFUL ===")
            except Exception as e:
                print(f"=== ROLLBACK: {e} ===")
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        if self.engine:
            await self.engine.dispose()


db_manager = None


def set_db_manager(manager):
    global db_manager
    db_manager = manager


def get_db_manager():
    return db_manager
