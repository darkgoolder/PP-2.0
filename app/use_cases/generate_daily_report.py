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

        # Проверка модели (идемпотентно)
        import os

        import torch

        from app.config import settings

        model_exists = os.path.exists(settings.model_path)
        model_accuracy = None

        if model_exists:
            try:
                checkpoint = torch.load(settings.model_path, map_location="cpu")
                model_accuracy = checkpoint.get("val_acc", None)
                logger.info(f"Model loaded. Accuracy: {model_accuracy}")
            except Exception as e:
                logger.warning(f"Model corrupted: {e}")
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
            f"Daily report generated for {start_of_day.date()}: {new_users_count} new users"
        )

        return report
