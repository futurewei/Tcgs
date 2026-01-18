from pydantic_settings import BaseSettings
from functools import lru_cache


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

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
