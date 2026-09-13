# backend/app/configs/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Ayarları (Settings) içeri aktarıyoruz
from app.configs.config import settings

logger = logging.getLogger("Database")

# Hardcoded URL yerine artık settings.POSTGRES_URL kullanıyoruz
SQLALCHEMY_DATABASE_URL = settings.POSTGRES_URL

logger.info("PostgreSQL veritabanı motoru başlatılıyor...")
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency (FastAPI router'larında kullanmak için)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()