"""
Хешер паролей с использованием bcrypt
"""

import bcrypt

from app.domain.interfaces import IPasswordHasher


class BcryptPasswordHasher(IPasswordHasher):
    """Хешер паролей на основе bcrypt"""

    def hash(self, password: str) -> str:
        """Хеширование пароля"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify(self, password: str, hashed: str) -> bool:
        """Проверка пароля"""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
