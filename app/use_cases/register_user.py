"""
Use Case: Регистрация пользователя
"""

import logging
import uuid
from datetime import datetime

from app.domain.entities import User, UserRole
from app.domain.interfaces import IUserRepository, IPasswordHasher
from app.domain.exceptions import UserAlreadyExistsError, InvalidCredentialsError

logger = logging.getLogger(__name__)


class RegisterUserUseCase:
    """Use case для регистрации пользователя"""
    
    def __init__(self, user_repository: IUserRepository, password_hasher: IPasswordHasher):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
    
    async def execute(self, username: str, email: str, password: str) -> dict:
        """
        Регистрация нового пользователя
        
        Returns:
            dict: Информация о созданном пользователе
        """
        # Валидация входных данных
        if not username or len(username) < 3:
            raise InvalidCredentialsError("Username must be at least 3 characters")
        
        if not email or "@" not in email:
            raise InvalidCredentialsError("Invalid email format")
        
        if not password or len(password) < 6:
            raise InvalidCredentialsError("Password must be at least 6 characters")
        
        # Проверка уникальности
        if await self.user_repository.exists_by_username(username):
            raise UserAlreadyExistsError(f"Username '{username}' already taken")
        
        if await self.user_repository.exists_by_email(email):
            raise UserAlreadyExistsError(f"Email '{email}' already registered")
        
        # Создание пользователя
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            hashed_password=self.password_hasher.hash(password),
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now()
        )
        
        # Сохранение
        await self.user_repository.save(user)
        
        logger.info(f"User registered: {username} ({email})")
        
        return user.to_dict()