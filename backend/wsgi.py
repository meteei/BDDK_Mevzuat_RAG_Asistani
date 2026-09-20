from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware

from app.routers.v1 import api_router
from app.configs.database import engine, Base

# --- YENİ EKLENEN İÇE AKTARMALAR ---
from app.tasks import start_scheduler
from app.clients.rustfs_client import RustFSClient


# -----------------------------------


def configure_middlewares(app: FastAPI) -> None:
    """CORS ve diğer middleware'leri yapılandırır."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


def init_routers(app: FastAPI) -> None:
    """Tüm API router'larını /api önekiyle kaydeder."""
    app.include_router(api_router, prefix="/api")


def init_database() -> None:
    """Veritabanı tablolarını (PostgreSQL) ayağa kaldırır."""
    Base.metadata.create_all(bind=engine)


def init_pages(app: FastAPI) -> None:
    """Frontend HTML sayfalarını tanımlar."""

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def root():
        # wsgi.py backend klasöründe, templates ise backend/app/templates içinde
        template_path = Path(__file__).resolve().parent / "templates" / "index.html"
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)


# --- YENİ EKLENEN MODÜLER FONKSİYON ---
def init_startup_events(app: FastAPI) -> None:
    """Uygulama başlarken çalışacak arka plan görevlerini ve altyapı kontrollerini tanımlar."""

    @app.on_event("startup")
    def startup_event():
        # 1. Veri Gölü (Data Lake) kovalarını kontrol et ve eksikleri otomatik aç
        RustFSClient.initialize_all_buckets()

        # 2. Arka plan yedekleme zamanlayıcısını (Scheduler) başlat
        start_scheduler()


# --------------------------------------


def create_app() -> FastAPI:
    """FastAPI uygulama fabrikası (Application Factory)."""

    # 1. Veritabanını başlat
    init_database()

    # 2. FastAPI objesini oluştur
    app = FastAPI(
        title="BDDK Regülasyon Asistanı",
        description="RAG Tabanlı Enterprise Kurumsal Asistan API",
        version="1.0.0",
    )

    # 3. Uygulama ayarlarını yükle
    configure_middlewares(app)
    init_routers(app)
    init_pages(app)

    # 4. Başlangıç (Startup) olaylarını yükle
    init_startup_events(app)  # <-- YENİ EKLENDİ

    return app


# Uvicorn veya Gunicorn bu app objesini arayacak
app = create_app()