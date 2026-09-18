import sys
import re
from pathlib import Path
import pymupdf  # Referans projede kullanıldığı gibi
from datetime import datetime, timezone

# Proje kök dizinini sys.path'e ekliyoruz
project_root = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, project_root)

from backend import get_milvus_client, create_collection_if_not_exists, COLLECTION_NAME
from backend import SessionLocal
from backend import UploadedDocument
from backend import OpenAIClient


def extract_text_from_pdf(pdf_path: str) -> str:
    """PyMuPDF ile metin çıkarma"""
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    return text


def run_ingestion():
    pdf_path = Path(project_root) / "static" / "imports" / "GeneratePdf.pdf"

    if not pdf_path.exists():
        print(f"[INGEST ERROR] PDF dosyası bulunamadı: {pdf_path}")
        print("Lütfen dosyayı static/imports dizinine yerleştirdiğinizden emin olun.")
        sys.exit(1)

    print(f"[INGEST] PDF dosyası okundu: {pdf_path.name}")
    print("[INGEST] 1. PDF okunuyor ve madde sınırlarına göre akıllı parçalanıyor...")

    # 1. DB kaydı ekleme/güncelleme (PostgreSQL)
    db = SessionLocal()
    file_size = pdf_path.stat().st_size

    # Eski kayıt varsa silip yenisini oluşturalım
    existing_doc = db.query(UploadedDocument).filter(UploadedDocument.filename == pdf_path.name).first()
    if existing_doc:
        db.delete(existing_doc)
        db.commit()

    db_doc = UploadedDocument(
        filename=pdf_path.name,
        file_type="pdf",
        file_size=file_size,
        status="processing",
        uploaded_at=datetime.now(timezone.utc)  # Eski utcnow() uyarısı düzeltildi
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    try:
        # 2. PyMuPDF ile Metni Çıkarma
        pdf_text = extract_text_from_pdf(str(pdf_path))

        # 3. MADDE başlıklarına göre metni yakalayan referans Regex deseni
        pattern = r"(MADDE\s+\d+[\s\S]*?)(?=(?:MADDE\s+\d+|\Z))"
        matches = re.findall(pattern, pdf_text)

        if not matches:
            maddeler_ham = re.split(r'\n(?=MADDE\s+\d+)', pdf_text)
            chunks = [m.strip() for m in maddeler_ham if len(m.strip()) > 20]
        else:
            chunks = [m.strip() for m in matches if len(m.strip()) > 20]

        print("2. Dokümanlar Milvus şemasına ve gerçek madde numaralarıyla metadata'ya dönüştürülüyor...")

        processed_chunks = []
        for chunk in chunks:
            # Metin içerisinden gerçek Madde numarasını yakalıyoruz (Örn: "MADDE 25")
            madde_match = re.search(r"MADDE\s+(\d+)", chunk)
            if madde_match:
                madde_no = int(madde_match.group(1))
                page_num = madde_no  # Şemadaki 'page' alanına referans olması için Madde No'yu atıyoruz
            else:
                page_num = 0  # Genel hüküm veya tanım kısmı

            processed_chunks.append({
                "text": chunk,
                "page": page_num
            })

        print(f"3. OpenAI Embeddings ile Embedding yapılıyor ve Milvus'a yazılıyor ({len(processed_chunks)} parça)...")

        # 4. Milvus Koleksiyon Kontrolü ve Sıfırlama
        client_temp = get_milvus_client()
        if client_temp.has_collection(COLLECTION_NAME):
            client_temp.drop_collection(COLLECTION_NAME)
            print(f"[INGEST] Eski koleksiyon silindi: {COLLECTION_NAME}")
        create_collection_if_not_exists()

        # 5. Embedding ve Veritabanı Yazma
        embeddings_model = OpenAIClient.get_embeddings()
        client = get_milvus_client()

        batch_size = 50
        total_chunks = len(processed_chunks)

        for i in range(0, total_chunks, batch_size):
            batch = processed_chunks[i:i + batch_size]
            texts = [c["text"] for c in batch]

            vectors = embeddings_model.embed_documents(texts)

            data = []
            for idx, doc in enumerate(batch):
                data.append({
                    "text": doc["text"],
                    "page": doc["page"],
                    "vector": vectors[idx],
                    "doc_id": db_doc.id,
                    "filename": db_doc.filename
                })

            client.insert(
                collection_name=COLLECTION_NAME,
                data=data
            )

        # Güncelleme: Durum Başarılı
        db_doc.status = "success"
        db.commit()
        print(f"✅ İŞLEM TAMAM! {total_chunks} adet BDDK maddesi başarıyla Milvus'a kaydedildi.")

    except Exception as e:
        # Güncelleme: Durum Hata
        db_doc.status = "error"
        db.commit()
        print(f"[INGEST ERROR] Yükleme sırasında bir hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_ingestion()