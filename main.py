from fastapi import FastAPI
from app.routers import rag_router
from app.configs.database import Base, engine

# 1. Veritabanı tablolarını otomatik oluştur (Eğer PostgreSQL'de tablo yoksa yaratır)
Base.metadata.create_all(bind=engine)

# 2. FastAPI Ana Uygulamasını Başlat
app = FastAPI(
    title="BDDK Mevzuat Asistanı API",
    description="RAG tabanlı kurumsal regülasyon asistanı arka plan servisi",
    version="1.0.0"
)

# 3. Yazdığımız router'ı (yönlendiriciyi) ana sisteme monte et
app.include_router(rag_router.router)

# 4. Sistem kontrol (Healthcheck) uç noktası
@app.get("/")
def root():
    return {"status": "success", "message": "BDDK Mevzuat Asistanı API Sistemleri Aktif!"}