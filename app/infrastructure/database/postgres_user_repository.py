"""
PostgreSQL реализация репозитория пользователей
"""

from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.domain.entities import User
from app.domain.interfaces import IUserRepository

from .models import UserModel


class PostgresUserRepository(IUserRepository):
    """PostgreSQL реализация репозитория пользователей"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> None:
        """Сохранить пользователя"""
        print("=== DEBUG save() ===")
        print(f"User to save: {user.username}, {user.email}")

        user_model = UserModel.from_domain(user)
        print(f"UserModel created: {user_model.username}")

        self.session.add(user_model)
        print("Added to session")

        await self.session.flush()
        print("Flushed - user should be in session")

    async def find_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user_model = result.scalar_one_or_none()
        return user_model.to_domain() if user_model else None

    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user_model = result.scalar_one_or_none()
        return user_model.to_domain() if user_model else None

    async def exists_by_username(self, username: str) -> bool:
        result = await self.session.execute(
            select(UserModel.id).where(UserModel.username == username)
        )
        return result.scalar_one_or_none() is not None

    async def exists_by_email(self, email: str) -> bool:
        result = await self.session.execute(
            select(UserModel.id).where(UserModel.email == email)
        )
        return result.scalar_one_or_none() is not None

    async def update_last_login(self, username: str) -> None:
        await self.session.execute(
            update(UserModel)
            .where(UserModel.username == username)
            .values(last_login=func.now())
        )
        await self.session.flush()

    async def get_all(self) -> List[User]:
        result = await self.session.execute(select(UserModel))
        users = result.scalars().all()
        return [u.to_domain() for u in users]
