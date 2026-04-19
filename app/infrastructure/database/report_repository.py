"""
Репозиторий для работы с ежедневными отчётами
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import DailyReport

from .models import DailyReportModel


class ReportRepository:
    """Репозиторий для хранения ежедневных отчётов"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, report: DailyReport) -> None:
        """Сохранить отчёт (идемпотентно: обновляет при повторном запуске)"""
        existing = await self.get_by_date(report.report_date)

        if existing:
            # Обновляем существующий отчёт
            await self.session.execute(
                update(DailyReportModel)
                .where(DailyReportModel.report_date == report.report_date)
                .values(
                    new_users_count=report.new_users_count,
                    total_predictions=report.total_predictions,
                    model_exists=report.model_exists,
                    model_accuracy=report.model_accuracy,
                )
            )
        else:
            # Создаём новый
            report_model = DailyReportModel.from_domain(report)
            self.session.add(report_model)

        await self.session.flush()

    async def get_by_date(self, report_date: datetime) -> Optional[DailyReport]:
        """Получить отчёт по дате"""
        # Нормализуем дату (начало дня)
        start_of_day = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = report_date.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        result = await self.session.execute(
            select(DailyReportModel).where(
                DailyReportModel.report_date >= start_of_day,
                DailyReportModel.report_date <= end_of_day,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all(self, limit: int = 30) -> List[DailyReport]:
        """Получить последние отчёты"""
        result = await self.session.execute(
            select(DailyReportModel)
            .order_by(DailyReportModel.report_date.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]
