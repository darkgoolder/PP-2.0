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
