# api/secrets.py
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Dict, Optional, List
import logging

from services.s3_secrets import secrets_manager, env_secrets
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/secrets", tags=["Secrets Management"])


class SecretRequest(BaseModel):
    """Запрос на сохранение секрета"""
    key: str
    value: str
    encrypt: bool = True
    save_to_s3: bool = True


class SecretResponse(BaseModel):
    """Ответ с секретом"""
    key: str
    value: Optional[str] = None
    exists: bool
    from_s3: bool = False


class SecretsBatchRequest(BaseModel):
    """Пакетный запрос секретов"""
    secrets: Dict[str, str]
    encrypt: bool = True


def verify_admin_token(admin_token: str = Header(...)):
    """Проверка admin токена"""
    if settings.admin_api_token:
        expected = settings.admin_api_token.get_secret_value()
        if admin_token != expected:
            raise HTTPException(status_code=403, detail="Invalid admin token")
    return True


@router.get("/health")
async def secrets_health():
    """Проверка статуса сервиса секретов"""
    return {
        "status": "healthy",
        "s3_available": bool(secrets_manager.load_secrets_from_s3()),
        "encryption_enabled": True,
        "backups_count": len(secrets_manager.list_backups())
    }


@router.post("/save", response_model=Dict)
async def save_secret(
    request: SecretRequest,
    admin: bool = Depends(verify_admin_token)
):
    """
    Сохранение секрета в S3
    
    - **key**: Имя секрета
    - **value**: Значение секрета
    - **encrypt**: Шифровать ли секрет
    - **save_to_s3**: Сохранять ли в S3
    """
    try:
        if request.save_to_s3:
            secrets_dict = {request.key: request.value}
            secrets_manager.save_secrets_to_s3(secrets_dict, encrypt=request.encrypt)
        
        env_secrets.set(request.key, request.value, save_to_s3=request.save_to_s3)
        
        return {
            "success": True,
            "key": request.key,
            "saved_to_s3": request.save_to_s3,
            "encrypted": request.encrypt
        }
    except Exception as e:
        logger.error(f"Ошибка сохранения секрета: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get/{key}", response_model=SecretResponse)
async def get_secret(
    key: str,
    admin: bool = Depends(verify_admin_token)
):
    """Получение секрета по ключу"""
    value = env_secrets.get(key)
    
    return SecretResponse(
        key=key,
        value=value,
        exists=value is not None,
        from_s3=True
    )


@router.post("/batch/save", response_model=Dict)
async def save_secrets_batch(
    request: SecretsBatchRequest,
    admin: bool = Depends(verify_admin_token)
):
    """Пакетное сохранение секретов"""
    try:
        secrets_manager.save_secrets_to_s3(request.secrets, encrypt=request.encrypt)
        
        for key, value in request.secrets.items():
            env_secrets.set(key, value, save_to_s3=False)
        
        return {
            "success": True,
            "count": len(request.secrets),
            "encrypted": request.encrypt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup")
async def create_backup(
    name: Optional[str] = None,
    admin: bool = Depends(verify_admin_token)
):
    """Создание бэкапа секретов"""
    try:
        backup_name = secrets_manager.backup_secrets(name)
        return {
            "success": True,
            "backup_name": backup_name,
            "message": f"Backup created: {backup_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{backup_name}")
async def restore_backup(
    backup_name: str,
    admin: bool = Depends(verify_admin_token)
):
    """Восстановление секретов из бэкапа"""
    try:
        secrets_manager.restore_secrets(backup_name)
        return {
            "success": True,
            "backup_name": backup_name,
            "message": f"Restored from: {backup_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups", response_model=List[str])
async def list_backups(
    admin: bool = Depends(verify_admin_token)
):
    """Список доступных бэкапов"""
    return secrets_manager.list_backups()


@router.post("/rotate/{key}")
async def rotate_secret(
    key: str,
    new_value: str,
    admin: bool = Depends(verify_admin_token)
):
    """Ротация секрета"""
    try:
        secrets_manager.rotate_secret(key, new_value)
        return {
            "success": True,
            "key": key,
            "message": f"Secret {key} rotated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/env")
async def export_to_env(
    admin: bool = Depends(verify_admin_token)
):
    """Экспорт секретов в .env файл"""
    try:
        env_secrets.export_to_env()
        return {
            "success": True,
            "message": "Secrets exported to .env file"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))