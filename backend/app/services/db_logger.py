# backend/app/services/db_logger.py
import logging
from sqlalchemy.orm import Session
from app.models.models import APILog

logger = logging.getLogger("DB_Logger")

def log_api_interaction(db: Session, prompt: str, response: str, time_taken_ms: int) -> APILog:
    """Kullanıcının sorusunu, sistemin cevabını ve geçen süreyi PostgreSQL'e kaydeder."""
    try:
        new_log = APILog(
            prompt=prompt,
            response=response,
            time_taken_ms=time_taken_ms
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        logger.info(f"Etkileşim veritabanına loglandı [Log ID: {new_log.id}]")
        return new_log
    except Exception as e:
        logger.error(f"Veritabanına log yazılırken hata oluştu: {str(e)}")
        db.rollback()
        raise e