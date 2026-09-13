# backend/app/main.py
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from app.configs.database import engine, Base
from app.models import models
from app.routers.v1 import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BDDK Regülasyon Asistanı",
    version="1.0.0",
    description="RAG Tabanlı Enterprise Kurumsal Asistan API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

# HTML Template Ayarları
templates = Jinja2Templates(directory="app/templates")

# Ana sayfaya girildiğinde API mesajı değil, HTML arayüzünü döndürüyoruz
@app.get(path="/", include_in_schema=False)
def read_root(request: Request):
    # Parametreleri açıkça isimlendiriyoruz (request=..., name=...)
    return templates.TemplateResponse(request=request, name="index.html")