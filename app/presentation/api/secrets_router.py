# app/presentation/api/secrets_router.py
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Dict, List, Optional

from app.use_cases import (
    SaveSecretUseCase,
    GetSecretUseCase,
    ListSecretsUseCase,
    DeleteSecretUseCase,
    CreateBackupUseCase,
    ListBackupsUseCase,
    RestoreBackupUseCase,
    RotateSecretUseCase,
)
from app.infrastructure import secret_repository
from app.config import settings

router = APIRouter(prefix="/secrets", tags=["Secrets"])


class SecretRequest(BaseModel):
    key: str
    value: str
    encrypt: bool = True


class SecretResponse(BaseModel):
    key: str
    value: Optional[str] = None
    exists: bool


class RotateRequest(BaseModel):
    new_value: str


def verify_admin_token(admin_token: str = Header(None)):
    """Проверка admin токена"""
    if settings.is_production:
        expected = settings.admin_api_token.get_secret_value() if settings.admin_api_token else None
        if not expected or admin_token != expected:
            raise HTTPException(status_code=403, detail="Invalid admin token")
    return True


def get_repository():
    """Dependency injection для репозитория"""
    return secret_repository


@router.get("/health")
async def health():
    """Health check для сервиса секретов"""
    return {"status": "healthy", "service": "secrets", "bucket": settings.secrets_bucket}


@router.post("/save")
async def save_secret(
    request: SecretRequest,
    admin: bool = Depends(verify_admin_token),
    repo=Depends(get_repository)
):
    """Сохранение секрета"""
    use_case = SaveSecretUseCase(repo)
    success = await use_case.execute(request.key, request.value, request.encrypt)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save secret")
    
    return {"success": True, "key": request.key}


@router.get("/get/{key}", response_model=SecretResponse)
async def get_secret(
    key: str,
    admin: bool = Depends(verify_admin_token),
    repo=Depends(get_repository)
):
    """Получение секрета"""
    use_case = GetSecretUseCase(repo)
    value = await use_case.execute(key)
    
    return SecretResponse(key=key, value=value, exists=value is not None)


@router.get("/list")
async def list_secrets(
    admin: bool = Depends(verify_admin_token),
    repo=Depends(get_repository)
):
    """Список всех ключей секретов"""
    use_case = ListSecretsUseCase(repo)
    keys = await use_case.execute()
    
    return {"secrets": keys, "count": len(keys)}


@router.delete("/delete/{key}")
async def delete_secret(
    key: str,
    admin: bool = Depends(verify_admin_token),
    repo=Depends(get_repository)
):
    """Удаление секрета"""
    use_case = DeleteSecretUseCase(repo)
    success = await use_case.execute(key)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Secret '{key}' not found")
    
    return {"success": True, "key": key, "deleted": True}


@router.post("/backup")
async def create_backup(
    name: Optional[str] = None,
    admin: bool = Depends(verify_admin_token),
    repo=Depends(get_repository)
):
    """Создание бэкапа секретов"""
    use_case = CreateBackupUseCase(repo)
    backup_name = await use_case.execute(name)
    
    return {"success": True, "backup_name": backup_name}


@router.get("/backups")
async def list_backups(
    admin: bool = Depends(verify_admin_token),
    repo=Depends(get_repository)
):
    """Список бэкапов"""
    use_case = ListBackupsUseCase(repo)
    backups = await use_case.execute()
    
    return {"backups": backups, "count": len(backups)}


@router.post("/restore/{backup_name}")
async def restore_backup(
    backup_name: str,
    admin: bool = Depends(verify_admin_token),
    repo=Depends(get_repository)
):
    """Восстановление из бэкапа"""
    use_case = RestoreBackupUseCase(repo)
    success = await use_case.execute(backup_name)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Backup '{backup_name}' not found")
    
    return {"success": True, "backup_name": backup_name, "restored": True}


@router.post("/rotate/{key}")
async def rotate_secret(
    key: str,
    request: RotateRequest,
    admin: bool = Depends(verify_admin_token),
    repo=Depends(get_repository)
):
    """Ротация секрета (создаёт бэкап)"""
    use_case = RotateSecretUseCase(repo)
    success = await use_case.execute(key, request.new_value)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to rotate secret '{key}'")
    
    return {"success": True, "key": key, "rotated": True}