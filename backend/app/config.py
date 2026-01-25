from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/tcgs"

    # JWT
    SECRET_KEY: str = "tcgs-dev-secret-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "tcgs-attachments"
    MINIO_SECURE: bool = False

    # App
    DEBUG: bool = True
    
    # Security - CORS allowed origins (comma-separated in env)
    CORS_ORIGINS: str = "http://localhost,http://localhost:80,http://localhost:5173,http://127.0.0.1,http://127.0.0.1:80,http://127.0.0.1:5173"
    
    # Rate limiting
    LOGIN_RATE_LIMIT: str = "5/minute"  # 每分钟最多5次登录尝试

    @property
    def cors_origins_list(self) -> List[str]:
        """将逗号分隔的CORS_ORIGINS转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
