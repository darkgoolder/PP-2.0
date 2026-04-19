"""
SQLAlchemy модели
"""

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, Integer, String
from sqlalchemy.sql import func

from app.domain.entities import User, UserRole

from .connection import Base


class UserRoleDB(enum.Enum):
    USER = "user"
    ADMIN = "admin"


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRoleDB), default=UserRoleDB.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> User:
        return User(
            id=self.id,
            username=self.username,
            email=self.email,
            hashed_password=self.hashed_password,
            role=UserRole(self.role.value),
            is_active=self.is_active,
            created_at=self.created_at,
            last_login=self.last_login,
        )

    @staticmethod
    def from_domain(user: User) -> "UserModel":
        return UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            role=UserRoleDB(user.role.value),
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
        )


class DailyReportModel(Base):
    """Модель для хранения ежедневных отчётов"""

    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(
        DateTime(timezone=True), unique=True, nullable=False, index=True
    )
    new_users_count = Column(Integer, default=0)
    total_predictions = Column(Integer, default=0)
    model_exists = Column(Boolean, default=False)
    model_accuracy = Column(Float, nullable=True)  # ← Float тоже нужен
    report_generated_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_domain(self):
        from app.domain.entities import DailyReport

        return DailyReport(
            report_date=self.report_date,
            new_users_count=self.new_users_count,
            total_predictions=self.total_predictions,
            model_exists=self.model_exists,
            model_accuracy=self.model_accuracy,
            report_generated_at=self.report_generated_at,
        )

    @staticmethod
    def from_domain(report):

        return DailyReportModel(
            report_date=report.report_date,
            new_users_count=report.new_users_count,
            total_predictions=report.total_predictions,
            model_exists=report.model_exists,
            model_accuracy=report.model_accuracy,
        )
