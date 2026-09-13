# backend/app/services/document_service.py
import os
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from app.clients.openai_client import get_embeddings
from app.clients.milvus_client import get_vector_store
from app.helpers.text_processor import text_processor

logger = logging.getLogger("Document_Service")

embeddings = get_embeddings()
vector_store = get_vector_store(embeddings)


def process_and_ingest_pdf(file_path: str):
    """Sisteme yeni yüklenen PDF dosyasını okur, yardımcı sınıf ile işler ve vektör DB'ye ekler."""
    logger.info(f"PDF işleme süreci başlatıldı: {file_path}")
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        logger.info(f"PDF yüklendi, toplam sayfa sayısı: {len(docs)}")

        filename = os.path.basename(file_path)
        if filename.startswith("temp_"):
            filename = filename[5:]

        logger.info("Metinler TextProcessor ile parçalanıyor...")
        splits = text_processor.process_documents(docs, filename)

        logger.info("Metadata tamamen filtreleniyor ve sadece Milvus şemasına uygun alanlar bırakılıyor...")
        cleaned_splits = []
        for doc in splits:
            # text_processor'dan gelen olası tüm gereksiz alanları (producer, creator, page vb.) eliyoruz.
            # Sadece Milvus koleksiyonunun tanımlı olduğu 'kaynak' ve 'madde_no' alanlarını alıyoruz.
            raw_metadata = doc.metadata if isinstance(doc.metadata, dict) else {}

            clean_metadata = {
                "kaynak": str(raw_metadata.get("kaynak", filename)),
                "madde_no": str(raw_metadata.get("madde_no", "Genel_Hukum"))
            }

            cleaned_doc = Document(
                page_content=doc.page_content,
                metadata=clean_metadata
            )
            cleaned_splits.append(cleaned_doc)

        logger.info(f"Parçalar Milvus veritabanına ekleniyor (Toplam parça: {len(cleaned_splits)})...")
        vector_store.add_documents(cleaned_splits)
        logger.info("✅ İşlem başarıyla tamamlandı ve tüm parçalar Milvus'a kaydedildi.")

        return len(cleaned_splits)
    except Exception as e:
        logger.error(f"PDF ingest edilirken kritik hata oluştu ({file_path}): {str(e)}")
        raise e