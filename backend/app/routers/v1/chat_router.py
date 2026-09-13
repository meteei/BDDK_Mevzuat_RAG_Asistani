# backend/app/routers/v1/chat_router.py
import time
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.configs.database import get_db
from app.models.models import APILog
from app.schemas.schemas import QueryRequest, QueryResponse
from app.services.chat_service import get_rag_response
from app.services.db_logger import log_api_interaction

logger = logging.getLogger("Chat_Router")

# Router tanımlaması (prefix'i main.py'den vereceğiz, burada sadece /chat kısmı kalabilir)
router = APIRouter(prefix="/chat", tags=["Chat & QA"])


@router.post("", response_model=QueryResponse)
def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    current_session_id = request.session_id or str(uuid.uuid4())

    logger.info(f"Soru isteği alındı [Session ID: {current_session_id}]: '{request.query}'")

    try:
        result = get_rag_response(user_query=request.query, session_id=current_session_id)
        time_taken = int((time.time() - start_time) * 1000)

        new_log = APILog(
            prompt=request.query,
            response=result["answer"],
            time_taken_ms=time_taken
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        logger.info(f"Soru başarıyla yanıtlandı ve loglandı [Log ID: {new_log.id}, Süre: {time_taken}ms]")

        return QueryResponse(
            log_id=new_log.id,
            query=request.query,
            answer=result["answer"],
            time_taken_ms=time_taken,
            sources=result["sources"],
            session_id=current_session_id
        )
    except Exception as e:
        logger.error(f"Soru işlenirken hata oluştu: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
def get_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info(f"Geçmiş loglar isteniyor [Skip: {skip}, Limit: {limit}]")
    logs = db.query(APILog).order_by(APILog.id.desc()).offset(skip).limit(limit).all()
    return logs


@router.put("/logs/{log_id}")
def update_log_feedback(log_id: int, is_helpful: bool, db: Session = Depends(get_db)):
    logger.info(f"Log ID {log_id} için geri bildirim güncelleniyor: is_helpful={is_helpful}")
    log = db.query(APILog).filter(APILog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Belirtilen ID'ye ait log bulunamadı.")
    log.is_helpful = is_helpful
    db.commit()
    db.refresh(log)
    return {"message": "Geri bildirim kaydedildi.", "log_id": log.id}


@router.delete("/logs/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    logger.info(f"Log silme isteği alındı [ID: {log_id}]")
    log = db.query(APILog).filter(APILog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Silinmek istenen log bulunamadı.")
    db.delete(log)
    db.commit()
    return {"message": f"Log (ID: {log_id}) başarıyla silindi."}