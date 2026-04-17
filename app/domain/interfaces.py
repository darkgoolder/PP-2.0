"""
Абстрактные интерфейсы (порты)
Определяют контракты для внешних зависимостей
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from .entities import User


class IImageClassifier(ABC):
    """Интерфейс классификатора изображений"""

    @abstractmethod
    def predict(self, image: Image.Image) -> Tuple[str, float, Dict[str, float]]:
        """
        Предсказание для одного изображения

        Returns:
            Tuple: (predicted_class, confidence, probabilities)
        """
        pass

    @abstractmethod
    def predict_batch(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
        """Пакетное предсказание"""
        pass

    @property
    @abstractmethod
    def device(self) -> str:
        """Устройство выполнения"""
        pass

    @property
    @abstractmethod
    def class_names(self) -> List[str]:
        """Список классов"""
        pass

    @property
    @abstractmethod
    def class_names_ru(self) -> Dict[str, str]:
        """Русские названия классов"""
        pass


class IUserRepository(ABC):
    """
    Интерфейс репозитория пользователей
    Определяет, как use case'ы работают с хранилищем пользователей
    """

    @abstractmethod
    async def save(self, user: User) -> None:
        """Сохранить пользователя"""
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """Найти пользователя по имени"""
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Найти пользователя по email"""
        pass

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Проверить существование пользователя по имени"""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Проверить существование пользователя по email"""
        pass

    @abstractmethod
    async def update_last_login(self, username: str) -> None:
        """Обновить время последнего входа"""
        pass

    @abstractmethod
    async def get_all(self) -> List[User]:
        """Получить всех пользователей"""
        pass


class IPasswordHasher(ABC):
    """Интерфейс хешера паролей"""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Хешировать пароль"""
        pass

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool:
        """Проверить пароль"""
        pass


# ============================================
# НОВЫЕ ИНТЕРФЕЙСЫ ДЛЯ СЕКРЕТОВ И S3
# ============================================

class ISecretRepository(ABC):
    """
    Интерфейс репозитория секретов
    Определяет, как use case'ы работают с хранилищем секретов в S3
    """

    @abstractmethod
    async def save_secret(self, key: str, value: str, encrypt: bool = True) -> bool:
        """Сохранить один секрет"""
        pass

    @abstractmethod
    async def get_secret(self, key: str) -> Optional[str]:
        """Получить секрет по ключу (расшифрованный)"""
        pass

    @abstractmethod
    async def delete_secret(self, key: str) -> bool:
        """Удалить секрет"""
        pass

    @abstractmethod
    async def list_secret_keys(self) -> List[str]:
        """Список всех ключей секретов"""
        pass

    @abstractmethod
    async def get_all_secrets(self) -> Dict[str, str]:
        """Получить все секреты (расшифрованные)"""
        pass

    @abstractmethod
    async def create_backup(self, name: Optional[str] = None) -> str:
        """Создать бэкап секретов"""
        pass

    @abstractmethod
    async def list_backups(self) -> List[Dict[str, Any]]:
        """Список бэкапов"""
        pass

    @abstractmethod
    async def restore_backup(self, name: str) -> bool:
        """Восстановить из бэкапа"""
        pass

    @abstractmethod
    async def rotate_secret(self, key: str, new_value: str) -> bool:
        """Ротация секрета (создаёт бэкап перед изменением)"""
        pass


class IEncryptionService(ABC):
    """Интерфейс сервиса шифрования для секретов"""

    @abstractmethod
    def encrypt(self, plain_text: str) -> str:
        """Шифрование текста"""
        pass

    @abstractmethod
    def decrypt(self, cipher_text: str) -> str:
        """Дешифрование текста"""
        pass


class IS3StorageService(ABC):
    """Интерфейс S3 хранилища (MinIO / AWS S3)"""

    @abstractmethod
    async def get_object(self, bucket: str, key: str) -> Optional[bytes]:
        """Получить объект из S3"""
        pass

    @abstractmethod
    async def put_object(self, bucket: str, key: str, data: bytes) -> bool:
        """Сохранить объект в S3"""
        pass

    @abstractmethod
    async def delete_object(self, bucket: str, key: str) -> bool:
        """Удалить объект из S3"""
        pass

    @abstractmethod
    async def list_objects(self, bucket: str, prefix: str = "") -> List[str]:
        """Список объектов в бакете"""
        pass

    @abstractmethod
    async def object_exists(self, bucket: str, key: str) -> bool:
        """Проверка существования объекта"""
        pass


class ISecretHealthCheck(ABC):
    """Интерфейс health check для сервиса секретов"""

    @abstractmethod
    async def check_connection(self) -> bool:
        """Проверка подключения к S3"""
        pass

    @abstractmethod
    async def check_encryption(self) -> bool:
        """Проверка работы шифрования"""
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Получить полный статус сервиса"""
        pass