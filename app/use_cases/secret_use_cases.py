# app/use_cases/secret_use_cases.py
import logging
from typing import Dict, List, Optional

from app.domain.interfaces import ISecretRepository

logger = logging.getLogger(__name__)


class SaveSecretUseCase:
    """Use case: сохранение секрета"""

    def __init__(self, repository: ISecretRepository):
        self.repository = repository

    async def execute(self, key: str, value: str, encrypt: bool = True) -> bool:
        """Выполнение сохранения секрета"""
        logger.info(f"Сохранение секрета: {key}")
        return await self.repository.save_secret(key, value, encrypt)


class GetSecretUseCase:
    """Use case: получение секрета"""

    def __init__(self, repository: ISecretRepository):
        self.repository = repository

    async def execute(self, key: str) -> Optional[str]:
        """Выполнение получения секрета"""
        logger.info(f"Получение секрета: {key}")
        return await self.repository.get_secret(key)


class ListSecretsUseCase:
    """Use case: список ключей секретов"""

    def __init__(self, repository: ISecretRepository):
        self.repository = repository

    async def execute(self) -> List[str]:
        """Выполнение получения списка ключей"""
        return await self.repository.list_secret_keys()


class DeleteSecretUseCase:
    """Use case: удаление секрета"""

    def __init__(self, repository: ISecretRepository):
        self.repository = repository

    async def execute(self, key: str) -> bool:
        """Выполнение удаления секрета"""
        logger.info(f"Удаление секрета: {key}")
        return await self.repository.delete_secret(key)


class CreateBackupUseCase:
    """Use case: создание бэкапа секретов"""

    def __init__(self, repository: ISecretRepository):
        self.repository = repository

    async def execute(self, name: Optional[str] = None) -> str:
        """Выполнение создания бэкапа"""
        logger.info("Создание бэкапа секретов")
        return await self.repository.create_backup(name)


class ListBackupsUseCase:
    """Use case: список бэкапов"""

    def __init__(self, repository: ISecretRepository):
        self.repository = repository

    async def execute(self) -> List[Dict]:
        """Выполнение получения списка бэкапов"""
        return await self.repository.list_backups()


class RestoreBackupUseCase:
    """Use case: восстановление из бэкапа"""

    def __init__(self, repository: ISecretRepository):
        self.repository = repository

    async def execute(self, name: str) -> bool:
        """Выполнение восстановления из бэкапа"""
        logger.info(f"Восстановление из бэкапа: {name}")
        return await self.repository.restore_backup(name)


class RotateSecretUseCase:
    """Use case: ротация секрета"""

    def __init__(self, repository: ISecretRepository):
        self.repository = repository

    async def execute(self, key: str, new_value: str) -> bool:
        """Выполнение ротации секрета"""
        logger.info(f"Ротация секрета: {key}")
        return await self.repository.rotate_secret(key, new_value)
