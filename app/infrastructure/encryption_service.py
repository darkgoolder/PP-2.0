# app/infrastructure/encryption_service.py
import logging
from pathlib import Path

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class FernetEncryptionService:
    """Реализация шифрования через Fernet"""
    
    def __init__(self, key_path: Path = None):
        if key_path is None:
            key_path = Path.home() / ".wagon_encryption_key"
        self.key_path = key_path
        self.cipher = self._get_cipher()
        logger.info(f"EncryptionService инициализирован: {self.key_path}")
    
    def _get_cipher(self) -> Fernet:
        """Получение или создание ключа шифрования"""
        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                key = f.read()
            logger.debug(f"Загружен существующий ключ шифрования")
        else:
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as f:
                f.write(key)
            self.key_path.chmod(0o600)
            logger.info(f"Создан новый ключ шифрования: {self.key_path}")
        return Fernet(key)
    
    def encrypt(self, plain_text: str) -> str:
        """Шифрование текста"""
        return self.cipher.encrypt(plain_text.encode()).decode()
    
    def decrypt(self, cipher_text: str) -> str:
        """Дешифрование текста"""
        return self.cipher.decrypt(cipher_text.encode()).decode()


# Глобальный экземпляр
encryption_service = FernetEncryptionService()