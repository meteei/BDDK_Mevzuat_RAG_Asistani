from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Hassas bilgiler: Değer atamıyoruz, .env'den gelmesi zorunlu
    POSTGRES_URL: str
    OPENAI_API_KEY: str
    RUSTFS_ACCESS_KEY: str
    RUSTFS_SECRET_KEY: str

    # Sistem/Port ayarları: Bunlar varsayılan olarak kalabilir
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    RUSTFS_ENDPOINT: str = "http://localhost:9000"

    # KURUMSAL RAG VERİ GÖLÜ (DATA LAKE) KOVALARI
    RUSTFS_BUCKET_NAME: str = "raw-documents"  # Orijinal PDF'ler
    RUSTFS_CHUNKS_BUCKET: str = "processed-chunks"  # Vektörleşmeden önceki JSON metinler
    RUSTFS_REPORTS_BUCKET: str = "generated-reports"  # LLM'in ürettiği indirilebilir raporlar
    RUSTFS_BACKUPS_BUCKET: str = "system-backups" # Veritabanı ve log otomatik yedekleri

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()