import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.configs.database import get_db
from app.models.models import APILog
from app.schemas.schemas import QueryRequest, QueryResponse
from app.services.rag_service import get_rag_response

# Router tanımlaması (Gelecekte farklı router'lar da ekleyebilmek için)
router = APIRouter(
    prefix="/api",
    tags=["RAG Assistant"]
)


# 1. CREATE - Soru Sorma ve Loglama (Mevcut Kodun)
@router.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    start_time = time.time()

    # 1. Beyne (Service katmanına) soruyu gönder ve sonucu al
    result = get_rag_response(user_query=request.query, session_id=request.session_id)

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
        log_id=new_log.id,  # YENİ EKLENEN SATIR
        query=request.query,
        answer=result["answer"],
        time_taken_ms=time_taken,
        sources=result["sources"]
    )


# 2. READ - Geçmiş Logları Getirme (YENİ)
@router.get("/logs")
def get_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Arayüzdeki yönetici paneli için geçmiş logları getirir."""
    logs = db.query(APILog).order_by(APILog.id.desc()).offset(skip).limit(limit).all()
    return logs


# 3. UPDATE - Log Güncelleme / Geri Bildirim (YENİ)
@router.put("/logs/{log_id}")
def update_log_feedback(log_id: int, is_helpful: bool, db: Session = Depends(get_db)):
    """Kullanıcının verdiği cevaba yaptığı olumlu/olumsuz geri bildirimi kaydeder."""
    log = db.query(APILog).filter(APILog.id == log_id).first()

    if not log:
        raise HTTPException(status_code=404, detail="Belirtilen ID'ye ait log bulunamadı.")

    # DİKKAT: Bu kodun çalışması için models.py içindeki APILog sınıfına
    # 'is_helpful = Column(Boolean, nullable=True)' sütununu eklemelisin.
    log.is_helpful = is_helpful
    db.commit()
    db.refresh(log)
    return {"message": "Geri bildirim başarıyla kaydedildi.", "log_id": log.id}


# 4. DELETE - Log Silme (YENİ)
@router.delete("/logs/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    """Veritabanından belirli bir log kaydını tamamen siler."""
    log = db.query(APILog).filter(APILog.id == log_id).first()

    if not log:
        raise HTTPException(status_code=404, detail="Silinmek istenen log bulunamadı.")

    db.delete(log)
    db.commit()
    return {"message": f"Log (ID: {log_id}) başarıyla silindi."}