import os
import shutil
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session

from app.configs.database import get_db
from app.models.models import APILog
from app.schemas.schemas import QueryRequest, QueryResponse
from app.services.rag_service import get_rag_response, process_and_ingest_pdf

# Router tanımlaması
router = APIRouter(
    prefix="/api",
    tags=["RAG Assistant"]
)


# 1. CREATE - Soru Sorma ve Loglama
@router.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    start_time = time.time()

    # Eğer frontend bir session_id göndermediyse (veya ilk defa giriyorsa) yeni bir tane üret
    current_session_id = request.session_id or str(uuid.uuid4())

    # 1. Beyne (Service katmanına) soruyu ve oturum kimliğini gönder
    result = get_rag_response(user_query=request.query, session_id=current_session_id)

    time_taken = int((time.time() - start_time) * 1000)

    # 2. Veritabanına işlemi kaydet (Loglama)
    new_log = APILog(
        prompt=request.query,
        response=result["answer"],
        time_taken_ms=time_taken
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)  # Kaydedilen verinin ID'sini almak için yeniliyoruz

    return QueryResponse(
        log_id=new_log.id,
        query=request.query,
        answer=result["answer"],
        time_taken_ms=time_taken,
        sources=result["sources"],
        session_id=current_session_id  # Arayüzün bu kimliği hatırlayabilmesi için geri döndürüyoruz
    )


# 2. READ - Geçmiş Logları Getirme
@router.get("/logs")
def get_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Arayüzdeki yönetici paneli için geçmiş logları getirir."""
    logs = db.query(APILog).order_by(APILog.id.desc()).offset(skip).limit(limit).all()
    return logs


# 3. UPDATE - Log Güncelleme / Geri Bildirim
@router.put("/logs/{log_id}")
def update_log_feedback(log_id: int, is_helpful: bool, db: Session = Depends(get_db)):
    """Kullanıcının verdiği cevaba yaptığı olumlu/olumsuz geri bildirimi kaydeder."""
    log = db.query(APILog).filter(APILog.id == log_id).first()

    if not log:
        raise HTTPException(status_code=404, detail="Belirtilen ID'ye ait log bulunamadı.")

    log.is_helpful = is_helpful
    db.commit()
    db.refresh(log)
    return {"message": "Geri bildirim başarıyla kaydedildi.", "log_id": log.id}


# 4. DELETE - Log Silme
@router.delete("/logs/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    """Veritabanından belirli bir log kaydını tamamen siler."""
    log = db.query(APILog).filter(APILog.id == log_id).first()

    if not log:
        raise HTTPException(status_code=404, detail="Silinmek istenen log bulunamadı.")

    db.delete(log)
    db.commit()
    return {"message": f"Log (ID: {log_id}) başarıyla silindi."}


# 5. CREATE - Dinamik Belge Yükleme (Ingestion)
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Arayüzden gönderilen PDF dosyasını geçici olarak kaydeder ve RAG sistemine indeksler."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF formatında dosyalar yüklenebilir.")

    temp_file_path = f"temp_{file.filename}"

    try:
        # Dosyayı sunucunun diskine geçici olarak yaz
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Servis katmanını çağırarak PDF'i parçala ve Milvus'a indeksle
        chunks_count = process_and_ingest_pdf(temp_file_path)

        return {
            "message": f"'{file.filename}' başarıyla yüklendi. Belge {chunks_count} parçaya bölünüp vektör veritabanına eklendi."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # İşlem bitince sunucudaki geçici PDF dosyasını temizle
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)