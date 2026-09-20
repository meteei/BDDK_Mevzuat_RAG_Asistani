# backend/app/tasks.py

import json
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from app.configs.database import SessionLocal
from app.models.models import ChatLog, UploadedDocument
from app.clients.rustfs_client import RustFSClient
from app.configs.config import settings

logger = logging.getLogger("Background_Tasks")


def backup_database_to_datalake():
    """
    PostgreSQL'deki kritik verileri (ChatLog ve UploadedDocument)
    çekip JSON formatında RustFS 'system-backups' kovasına yedekler.
    """
    db = SessionLocal()
    try:
        logger.info("[Backup Task] Otomatik veritabanı yedekleme işlemi başlatılıyor...")

        chat_logs = db.query(ChatLog).all()
        documents = db.query(UploadedDocument).all()

        backup_data = {
            "backup_timestamp": datetime.utcnow().isoformat(),
            "chat_logs": [
                {
                    "id": log.id,
                    "request_body": log.request_body,
                    "response_body": log.response_body,
                    "duration": log.duration,
                    "log_level": log.log_level,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "is_helpful": log.is_helpful
                } for log in chat_logs
            ],
            "uploaded_documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "status": doc.status,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
                } for doc in documents
            ]
        }

        json_bytes = json.dumps(backup_data, ensure_ascii=False, indent=2).encode("utf-8")

        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_backup_{timestamp_str}.json"

        target_bucket = getattr(settings, "RUSTFS_BACKUPS_BUCKET", "system-backups")

        RustFSClient.upload_file(
            file_bytes=json_bytes,
            object_name=backup_filename,
            bucket_name=target_bucket
        )

        logger.info(f"[Backup Task] Veritabanı başarıyla Data Lake'e yedeklendi: {backup_filename}")

    except Exception as e:
        logger.error(f"[Backup Task Error] Yedekleme sırasında hata oluştu: {e}")
    finally:
        db.close()


def start_scheduler():
    """
    Arka plan görevlerini başlatan zamanlayıcı motor.
    FastAPI başlatıldığında main.py tarafından çağrılır.
    """
    scheduler = BackgroundScheduler()

    # Yedekleme görevini her 12 saatte bir çalışacak şekilde kur
    # (Eğer hemen test etmek istersen 'hours=12' kısmını 'minutes=1' yapabilirsin)
    scheduler.add_job(backup_database_to_datalake, 'interval', hours=12)

    scheduler.start()
    logger.info("[Scheduler] Arka plan görevleri başlatıldı (DB Yedekleme: 12 saatte bir).")