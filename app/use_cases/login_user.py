"""
Use Case: Аутентификация пользователя
"""

import logging

from app.domain.interfaces import IUserRepository, IPasswordHasher
from app.domain.exceptions import UserNotFoundError, InvalidCredentialsError, UserNotActiveError

logger = logging.getLogger(__name__)


class LoginUserUseCase:
    """Use case для аутентификации пользователя"""
    
    def __init__(self, user_repository: IUserRepository, password_hasher: IPasswordHasher):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
    
    async def execute(self, username: str, password: str) -> dict:
        """
        Аутентификация пользователя
        
        Returns:
            dict: Информация о пользователе
        """
        # Поиск пользователя
        user = await self.user_repository.find_by_username(username)
        
        if not user:
            raise InvalidCredentialsError("Invalid username or password")
        
        # Проверка пароля
        if not user.verify_password(password, self.password_hasher):
            raise InvalidCredentialsError("Invalid username or password")
        
        # Проверка активности
        if not user.is_active:
            raise UserNotActiveError("User account is deactivated")
        
        # Обновление времени последнего входа
        await self.user_repository.update_last_login(username)
        
        logger.info(f"User logged in: {username}")
        
        return user.to_dict()