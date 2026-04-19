from app.infrastructure.encryption_service import (
    FernetEncryptionService,
    encryption_service,
)
from app.infrastructure.s3_storage import S3StorageService, s3_storage
from app.infrastructure.secret_repository_s3 import (
    S3SecretRepository,
    init_secret_repository,
)

# Создаём глобальный экземпляр репозитория
secret_repository = init_secret_repository(s3_storage, encryption_service)

__all__ = [
    "S3StorageService",
    "s3_storage",
    "FernetEncryptionService",
    "encryption_service",
    "S3SecretRepository",
    "secret_repository",
    "init_secret_repository",
]
