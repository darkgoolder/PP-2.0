import os
from pathlib import Path
from typing import List


class Settings:
    """Простая конфигурация проекта"""
    
    def __init__(self):
        self._load_env()
        
        self.app_env = os.getenv("APP_ENV", "dev")
        self.debug = os.getenv("DEBUG", "True").lower() == "true"
        self.api_prefix = os.getenv("API_PREFIX", "/api/v1")
        self.api_title = os.getenv("API_TITLE", "Wagon API")
        self.model_path = Path(os.getenv("MODEL_PATH", "./models/best_model.pth"))
        self.class_names = os.getenv("CLASS_NAMES", "pered,zad,none")
        self.database_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        self.secret_key = os.getenv("SECRET_KEY", "change-me")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        self.batch_size = int(os.getenv("BATCH_SIZE", "32"))
        self.num_epochs = int(os.getenv("NUM_EPOCHS", "15"))
        self.learning_rate = float(os.getenv("LEARNING_RATE", "1e-4"))
        
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.minio_secure = os.getenv("MINIO_SECURE", "False").lower() == "true"
        self.minio_region = os.getenv("MINIO_REGION", "us-east-1")
        self.secrets_bucket = os.getenv("SECRETS_BUCKET", "wagon-secrets")
        
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_env(self):
        """Загрузка .env файла (UTF-8)"""
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        os.environ[key.strip()] = val.strip()
    
    @property
    def class_names_list(self) -> List[str]:
        return [c.strip() for c in self.class_names.split(",")]
    
    @property
    def CLASS_NAMES(self) -> List[str]:
        return self.class_names_list
    
    @property
    def num_classes(self) -> int:
        return len(self.class_names_list)
    
    @property
    def device(self) -> str:
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except:
            return "cpu"
    
    @property
    def is_development(self) -> bool:
        return self.app_env == "dev"
    
    def validate_file_extension(self, filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in {'.jpg', '.jpeg', '.png', '.bmp'}
    
    def get_class_index(self, class_name: str) -> int:
        return self.class_names_list.index(class_name)
    
    # @property
    # def minio_config(self) -> dict:
    #     return {
    #         "endpoint": self.minio_endpoint,
    #         "access_key": self.minio_access_key,
    #         "secret_key": self.minio_secret_key,
    #         "secure": self.minio_secure,
    #         "region": self.minio_region,
    #     }

    @property
    def minio_config(self) -> dict:
        return {
            "endpoint": self.minio_endpoint,
            "access_key": "minioadmin",
            "secret_key": "minioadmin",
            "secure": self.minio_secure,
            "region": self.minio_region,
        }


settings = Settings()