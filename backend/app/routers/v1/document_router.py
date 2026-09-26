import os
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session

from app.configs.database import get_db
from app.services.document_service import list_documents, delete_document, process_upload

router = APIRouter()

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.csv', '.txt'}


# 1. GET /documents — Yüklü Belgeleri Listeleme

@router.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    """
    Sisteme yüklenmiş olan tüm belgeleri (PDF, Word, CSV, TXT)
    veritabanından çekerek listeler.
    """
    try:
        return list_documents(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Belgeler listelenirken hata oluştu: {str(e)}")


# 2. DELETE /documents/{doc_id} — Belge Silme

@router.delete("/documents/{doc_id}")
def remove_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Belirtilen belgeyi hem SQL Server'dan siler hem de
    Milvus vektör veritabanındaki o belgeye ait tüm chunk'ları temizler.
    """
    try:
        result = delete_document(doc_id, db)
        if result is None:
            raise HTTPException(status_code=404, detail="Belge bulunamadı.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Belge silinirken hata oluştu: {str(e)}")


# 3. POST /upload — Belge Yükleme

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Yüklenen PDF, DOCX, CSV ve TXT dosyalarını kabul eder,
    metinlerini çıkarıp TextProcessor (Regex) ile parçalar, OpenAI ile embed eder ve Milvus'a yazar.
    Dosya durumunu veritabanı (PostgreSQL) üzerinden takip eder.
    """
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen dosya türü. Kabul edilen türler: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    file_content = await file.read()

    try:
        result = process_upload(file.filename, file_ext, file_content, db)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"'{file.filename}' işlenirken ve indekslenirken hata oluştu: {str(e)}"
        )