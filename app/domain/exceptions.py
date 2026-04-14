"""
Доменные исключения
"""


class DomainException(Exception):
    """Базовое исключение домена"""

    pass


class InvalidImageException(DomainException):
    """Некорректное изображение"""

    pass


class ModelNotFoundException(DomainException):
    """Модель не найдена"""

    pass


class ModelNotLoadedException(DomainException):
    def __init__(self, message: str = "Модель не загружена. Сначала обучите модель"):
        self.message = message
        super().__init__(message)


class TrainingException(DomainException):
    """Ошибка при обучении"""

    pass


class DataPreparationException(DomainException):
    """Ошибка при подготовке данных"""

    pass


class UserNotFoundError(DomainException):
    """Пользователь не найден"""

    pass


class UserAlreadyExistsError(DomainException):
    """Пользователь уже существует"""

    pass


class InvalidCredentialsError(DomainException):
    """Неверные учетные данные"""

    pass


class UserNotActiveError(DomainException):
    """Пользователь не активен"""

    pass
