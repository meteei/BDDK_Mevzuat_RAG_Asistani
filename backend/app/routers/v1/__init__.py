from fastapi import APIRouter

# Doğru import yolları (Bulunduğu dizinden veya app klasöründen almalı)
from app.routers.v1.chat_router import router as chat_router
from app.routers.v1.document_router import router as document_router

api_router = APIRouter()

# Router'ları ana API router'ına ekliyoruz
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(document_router, prefix="/documents", tags=["Documents"])