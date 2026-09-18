from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.configs.config import settings

# PostgreSQL bağlantısı için SQLAlchemy motoru oluşturma
engine = create_engine(
    settings.POSTGRES_URL,
    pool_pre_ping=True,   # Kopan bağlantıları otomatik tespit eder ve yeniler
    pool_recycle=1800,    # Açık bağlantıları 30 dakikada bir tazeleyerek timeout'u önler
)

# Senkron veritabanı oturum (Session) oluşturma
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modeller için temel sınıf
Base = declarative_base()

# FastAPI Dependency (Bağımlılık Enjeksiyonu) olarak veritabanı oturumu yönetimi
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()