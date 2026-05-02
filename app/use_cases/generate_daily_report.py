"""
Use Case: Генерация ежедневного отчёта (идемпотентный)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.domain.entities import DailyReport
from app.domain.interfaces import IUserRepository
from app.infrastructure.database.report_repository import ReportRepository

logger = logging.getLogger(__name__)


class GenerateDailyReportUseCase:
    """Use case для генерации ежедневного отчёта (идемпотентный)"""

    def __init__(
        self, user_repository: IUserRepository, report_repository: ReportRepository
    ):
        self.user_repository = user_repository
        self.report_repository = report_repository

    async def execute(self, target_date: Optional[datetime] = None) -> DailyReport:
        """
        Генерация отчёта для указанной даты

        Args:
            target_date: Дата отчёта (по умолчанию - вчера)

        Returns:
            DailyReport: Сгенерированный отчёт
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)

        # Нормализуем дату (начало и конец дня)
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # Подсчёт новых пользователей за день
        users = await self.user_repository.get_users_by_date_range(
            start_of_day, end_of_day
        )
        new_users_count = len(users)

        # Проверка модели и получение точности (идемпотентно)
        import os

        import torch

        from app.config import settings

        model_exists = os.path.exists(settings.model_path)
        model_accuracy = None

        if model_exists:
            try:
                checkpoint = torch.load(settings.model_path, map_location="cpu")

                # Пробуем получить точность из разных возможных ключей
                if isinstance(checkpoint, dict):
                    # Вариант 1: ключ 'val_acc'
                    if "val_acc" in checkpoint:
                        model_accuracy = checkpoint["val_acc"]
                    # Вариант 2: ключ 'accuracy'
                    elif "accuracy" in checkpoint:
                        model_accuracy = checkpoint["accuracy"]
                    # Вариант 3: ключ 'best_val_acc'
                    elif "best_val_acc" in checkpoint:
                        model_accuracy = checkpoint["best_val_acc"]
                    # Вариант 4: ключ 'model_accuracy'
                    elif "model_accuracy" in checkpoint:
                        model_accuracy = checkpoint["model_accuracy"]

                    # Если нашли точность, округляем до 4 знаков
                    if model_accuracy is not None:
                        model_accuracy = round(float(model_accuracy), 4)
                        logger.info(f"Model accuracy: {model_accuracy}")
                    else:
                        logger.warning(
                            "No accuracy found in model checkpoint. Available keys: %s",
                            list(checkpoint.keys()),
                        )
                else:
                    logger.warning(
                        "Checkpoint is not a dictionary, type: %s", type(checkpoint)
                    )

            except Exception as e:
                logger.warning(f"Model corrupted or cannot load: {e}")
                model_exists = False

        # TODO: Подсчёт предсказаний (если добавите логирование)
        total_predictions = 0

        report = DailyReport(
            report_date=start_of_day,
            new_users_count=new_users_count,
            total_predictions=total_predictions,
            model_exists=model_exists,
            model_accuracy=model_accuracy,
        )

        # Сохраняем отчёт (идемпотентно)
        await self.report_repository.save(report)

        logger.info(
            f"Daily report generated for {start_of_day.date()}: {new_users_count} new users, model_accuracy: {model_accuracy}"
        )

        return report
