# backend/app/routers/v1/__init__.py
from fastapi import APIRouter
from app.routers.v1.chat_router import router as chat_router
from app.routers.v1.document_router import router as document_router

# Tüm v1 router'larını toplayan ana yönlendirici
api_router = APIRouter()

# Alt router'ları ekliyoruz (chat_router içinde "/chat", document_router içinde "/documents" tanımlı)
api_router.include_router(chat_router, prefix="/v1")
api_router.include_router(document_router, prefix="/v1")