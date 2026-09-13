# backend/app/routers/v1/document_router.py
import os
import shutil
import logging
from fastapi import APIRouter, HTTPException, File, UploadFile

from app.services.document_service import process_and_ingest_pdf

logger = logging.getLogger("Document_Router")

router = APIRouter(prefix="/documents", tags=["Document Management"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        logger.warning(f"Geçersiz dosya formatı reddedildi: {file.filename}")
        raise HTTPException(status_code=400, detail="Sadece PDF formatında dosyalar yüklenebilir.")

    temp_file_path = f"temp_{file.filename}"
    logger.info(f"PDF yükleme süreci başlatıldı: {file.filename}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks_count = process_and_ingest_pdf(temp_file_path)
        logger.info(f"'{file.filename}' başarıyla işlendi. Parça sayısı: {chunks_count}")

        return {
            "message": f"'{file.filename}' başarıyla yüklendi. Belge {chunks_count} parçaya bölünüp veritabanına eklendi."
        }
    except Exception as e:
        logger.error(f"PDF yükleme/işleme sırasında hata oluştu ({file.filename}): {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)