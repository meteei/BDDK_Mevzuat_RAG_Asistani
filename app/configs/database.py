from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Veritabanı URL'miz (Eski kodumuzdan taşıdık)
DATABASE_URL = "postgresql://admin:adminpassword@localhost:5432/rag_logs"

# Motor (Engine) ve Oturum (Session) ayarları
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tablolarımızın miras alacağı ana sınıf
Base = declarative_base()

# İşlem bitince veritabanı bağlantısını güvenlice kapatan yardımcı fonksiyon
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()