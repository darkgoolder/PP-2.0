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
    """Модель не загружена"""
    pass


class TrainingException(DomainException):
    """Ошибка при обучении"""
    pass


class DataPreparationException(DomainException):
    """Ошибка при подготовке данных"""
    pass