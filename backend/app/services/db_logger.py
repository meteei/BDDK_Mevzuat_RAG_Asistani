# backend/app/services/db_logger.py

from datetime import datetime
from app.configs.database import SessionLocal
from app.models.models import ChatLog


def log_to_db_background(
    request_body: str,
    response_body: str,
    duration: float,
    log_level: str = "INFO"
) -> None:
    """
    Sanal ortamda engellemeyen arka plan görevi (Background Task) olarak çalışıp,
    istek detaylarını veritabanındaki chat_logs tablosuna kaydeder.
    Her çağrıda yeni bir izole veritabanı oturumu oluşturur ve kapatır.
    """
    db = SessionLocal()
    try:
        chat_log = ChatLog(
            request_body=request_body,
            response_body=response_body,
            duration=duration,
            log_level=log_level,
            timestamp=datetime.utcnow()
        )
        db.add(chat_log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[DB LOGGER ERROR] Failed to save log to database: {e}")
    finally:
        db.close()