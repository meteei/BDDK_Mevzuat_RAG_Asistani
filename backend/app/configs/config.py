# backend/app/configs/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Veritabanı (PostgreSQL) Ayarları
    POSTGRES_URL: str = "postgresql://admin:adminpassword@localhost:5432/rag_logs"

    # Milvus Ayarları
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530

    # OpenAI Ayarları
    OPENAI_API_KEY: str

    # RustFS (MinIO / S3) Ayarları
    RUSTFS_ENDPOINT: str = "http://localhost:9000"
    RUSTFS_ACCESS_KEY: str = "minioadmin"
    RUSTFS_SECRET_KEY: str = "minioadmin"
    RUSTFS_BUCKET_NAME: str = "milvus-data"

    # Ortam değişkenlerini (.env) yükleme ayarı
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Proje genelinde kullanılacak ayar nesnesi
settings = Settings()