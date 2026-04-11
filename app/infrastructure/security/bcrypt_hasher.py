"""
Хешер паролей
"""

import bcrypt

from app.domain.interfaces import IPasswordHasher


class BcryptPasswordHasher(IPasswordHasher):
    def hash(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed.encode('utf-8')
        )