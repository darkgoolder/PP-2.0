"""
Реализация репозитория пользователей (хранилище в памяти/файле)
Без БД! Используем JSON файл для хранения
"""

import json
import os
import logging
from typing import Optional, List
from datetime import datetime

from app.domain.entities import User, UserRole
from app.domain.interfaces import IUserRepository
from app.domain.exceptions import UserNotFoundError

logger = logging.getLogger(__name__)


class JsonUserRepository(IUserRepository):
    """
    Реализация репозитория пользователей с хранением в JSON файле
    Не требует БД, использует файловую систему
    """
    
    def __init__(self, file_path: str = "users.json"):
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Создать файл если не существует"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)
            logger.info(f"Created users file: {self.file_path}")
    
    def _load_users(self) -> List[dict]:
        """Загрузить пользователей из файла"""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_users(self, users: List[dict]):
        """Сохранить пользователей в файл"""
        with open(self.file_path, 'w') as f:
            json.dump(users, f, indent=2, default=str)
    
    def _dict_to_user(self, data: dict) -> User:
        """Преобразовать словарь в User"""
        return User(
            id=data['id'],
            username=data['username'],
            email=data['email'],
            hashed_password=data['hashed_password'],
            role=UserRole(data.get('role', 'user')),
            is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None
        )
    
    async def save(self, user: User) -> None:
        """Сохранить пользователя"""
        users = self._load_users()
        
        # Проверяем, существует ли уже
        for i, u in enumerate(users):
            if u['username'] == user.username:
                users[i] = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'hashed_password': user.hashed_password,
                    'role': user.role.value,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
                self._save_users(users)
                return
        
        # Добавляем нового
        users.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'hashed_password': user.hashed_password,
            'role': user.role.value,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        })
        self._save_users(users)
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """Найти пользователя по имени"""
        users = self._load_users()
        for u in users:
            if u['username'] == username:
                return self._dict_to_user(u)
        return None
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Найти пользователя по email"""
        users = self._load_users()
        for u in users:
            if u['email'] == email:
                return self._dict_to_user(u)
        return None
    
    async def exists_by_username(self, username: str) -> bool:
        """Проверить существование"""
        users = self._load_users()
        return any(u['username'] == username for u in users)
    
    async def exists_by_email(self, email: str) -> bool:
        """Проверить существование email"""
        users = self._load_users()
        return any(u['email'] == email for u in users)
    
    async def update_last_login(self, username: str) -> None:
        """Обновить время последнего входа"""
        users = self._load_users()
        for u in users:
            if u['username'] == username:
                u['last_login'] = datetime.now().isoformat()
                break
        self._save_users(users)
    
    async def get_all(self) -> List[User]:
        """Получить всех пользователей"""
        users = self._load_users()
        return [self._dict_to_user(u) for u in users]