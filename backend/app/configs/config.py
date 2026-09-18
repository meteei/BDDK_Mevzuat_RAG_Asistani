from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_URL: str = "postgresql://admin:adminpassword@localhost:5432/rag_logs"

    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530

    OPENAI_API_KEY: str

    RUSTFS_ENDPOINT: str = "http://localhost:9000"
    RUSTFS_ACCESS_KEY: str = "rustfsadmin"
    RUSTFS_SECRET_KEY: str = "rustfsadmin"
    RUSTFS_BUCKET_NAME: str = "milvus-data"

    # KRİTİK GÜNCELLEME: Alembic veya FastAPI nereden başlatılırsa başlatılsın
    # .env dosyasını bulabilmesi için olası tüm yolları (rotaları) ekledik.
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()