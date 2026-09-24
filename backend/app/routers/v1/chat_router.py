import time
from typing import Callable
from fastapi import Request, Response, APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.chat_service import generate_response
from app.services.db_logger import log_to_db_background
from app.configs.database import get_db
from app.models.models import ChatLog  # Kendi model adına göre (örn: ChatHistory) güncelleyebilirsin


class LoggingRoute(APIRoute):
    """
    Her chat isteğini ve yanıtını FastAPI'nin yaşam döngüsüne müdahale ederek 
    otomatik ve asenkron bir şekilde DB'ye loglayan özel route sınıfı.
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()

            # Gelen isteğin gövdesini (body) yakalıyoruz
            body = await request.body()
            request_body_str = body.decode("utf-8") if body else ""

            # Asıl endpoint fonksiyonunu çalıştırıp yanıtı alıyoruz
            response: Response = await original_route_handler(request)

            # İşlem süresini hesaplıyoruz
            duration = time.time() - start_time

            # Üretilen yanıtın gövdesini alıyoruz
            response_body_str = ""
            if hasattr(response, "body"):
                response_body_str = response.body.decode("utf-8")

            # Arka plan görevleri (BackgroundTasks) yöneticisini ayarlıyoruz
            if response.background is None:
                bg_tasks = BackgroundTasks()
                response.background = bg_tasks
            else:
                bg_tasks = response.background

            # İstek bittikten hemen sonra arka planda veritabanı loglamasını tetikliyoruz
            bg_tasks.add_task(
                log_to_db_background,
                request_body=request_body_str,  # DÜZELTİLDİ
                response_body=response_body_str,  # DÜZELTİLDİ
                duration=int(duration)  # DÜZELTİLDİ (SQL'deki Integer tipine çevrildi)

            )

            return response

        return custom_route_handler


# Router tanımlamasında özel LoggingRoute sınıfımızı aktif ediyoruz
router = APIRouter(route_class=LoggingRoute, tags=["Chat & QA"])


@router.post("/chat", response_model=ChatResponse, summary="BDDK Regülasyon Asistanı RAG Yanıtı")
async def chat(request: ChatRequest):
    """
    Kullanıcının sorularını kabul eden ve Milvus ile OpenAI kullanarak
    anlamsal RAG yanıtı dönen ana sohbet endpoint'i.
    """
    try:
        # Chat servisi üzerinden RAG yanıtını üretiyoruz
        result = generate_response(request.message, request.session_id)

        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Rehber koleksiyonu henüz oluşturulmamış. Lütfen önce bir döküman yükleyin."
            )

        return ChatResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Sohbet işlenirken bir hata oluştu: {str(e)}"
        )


# -------------------------------------------------------------------
# YENİ EKLENEN ENDPOINT'LER (GEÇMİŞ VE GERİ BİLDİRİM)
# -------------------------------------------------------------------

@router.get("/logs", summary="Geçmiş sohbet loglarını getirir")
async def get_logs(limit: int = 10, skip: int = 0, db: Session = Depends(get_db)):
    """
    Veritabanına asenkron olarak kaydedilen sohbet geçmişini (Admin ve arayüz için)
    en yeniden en eskiye doğru sıralı şekilde getirir.
    """
    try:
        logs = db.query(ChatLog).order_by(ChatLog.id.desc()).offset(skip).limit(limit).all()
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Loglar çekilirken hata oluştu: {str(e)}")


@router.put("/logs/{log_id}", summary="Kullanıcı geri bildirimini günceller")
async def update_feedback(log_id: int, is_helpful: bool, db: Session = Depends(get_db)):
    """
    Kullanıcının RAG yanıtını faydalı bulup bulmadığını (RLHF için)
    ilgili log kaydına işler (is_helpful: true/false).
    """
    try:
        log = db.query(ChatLog).filter(ChatLog.id == log_id).first()

        if not log:
            raise HTTPException(status_code=404, detail=f"{log_id} numaralı log bulunamadı.")

        # Veritabanındaki satırı güncelliyoruz
        log.is_helpful = is_helpful
        db.commit()

        return {
            "message": "Geri bildirim başarıyla kaydedildi.",
            "log_id": log_id,
            "is_helpful": is_helpful
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Geri bildirim güncellenirken hata oluştu: {str(e)}")

@router.delete("/logs/{log_id}", summary="Belirtilen sohbet logunu siler")
async def delete_log(log_id: int, db: Session = Depends(get_db)):
        """
        Belirtilen ID'ye sahip sohbet kaydını (ChatLog) veritabanından kalıcı olarak siler.
        """
        try:
            log = db.query(ChatLog).filter(ChatLog.id == log_id).first()
            if not log:
                raise HTTPException(status_code=404, detail=f"{log_id} numaralı silinecek log bulunamadı.")

            db.delete(log)
            db.commit()
            return {"message": f"{log_id} numaralı sohbet başarıyla silindi.", "status": "success"}
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Log silinirken hata oluştu: {str(e)}")