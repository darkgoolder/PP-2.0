"""
Настройка логирования
"""

import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None):
    """
    Настройка логирования для приложения

    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
    """
    log_level = level or logging.INFO

    # Настройка формата
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Обработчик для stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Уменьшаем логи от библиотек
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)

    return root_logger
