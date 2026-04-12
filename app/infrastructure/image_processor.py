"""
Утилиты для работы с изображениями
"""

import io
import logging
import os

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageFile

# Разрешаем загрузку усеченных изображений
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)


def validate_image_file(file: UploadFile, settings) -> bool:
    """
    Проверка валидности файла изображения

    Args:
        file: Загруженный файл
        settings: Настройки приложения

    Returns:
        True если файл валиден

    Raises:
        HTTPException при ошибках валидации
    """
    # Проверяем расширение
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_EXTENSION",
                "message": f"Неподдерживаемый формат. Разрешенные: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            },
        )

    # Проверяем размер
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"Файл слишком большой. Максимум: {settings.MAX_UPLOAD_SIZE // (1024*1024)} MB",
            },
        )

    return True


def process_image(file: UploadFile) -> Image.Image:
    """
    Загрузка и предобработка изображения

    Args:
        file: Загруженный файл

    Returns:
        PIL Image объект

    Raises:
        HTTPException при ошибках загрузки
    """
    try:
        # Читаем файл
        contents = file.file.read()

        # Пытаемся открыть как изображение
        image = Image.open(io.BytesIO(contents))

        # Проверяем, что изображение можно прочитать
        image.verify()

        # Переоткрываем (после verify нужно заново)
        image = Image.open(io.BytesIO(contents))

        return image

    except Exception as e:
        logger.error(f"Ошибка загрузки изображения: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_IMAGE",
                "message": "Файл не является корректным изображением",
            },
        )
