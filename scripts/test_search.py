# scripts/test_search.py

import sys
from pathlib import Path

# Proje kök dizini içerisindeki 'backend' klasörünü sys.path'e ekliyoruz
backend_path = str(Path(__file__).resolve().parents[1] / "backend")
sys.path.insert(0, backend_path)

# 1. Uygulama Ayarları
from app.configs.config import settings
# 2. Vektör Veritabanı İstemcisi ve Koleksiyon Adı
from app.clients.milvus_client import get_milvus_client, COLLECTION_NAME
# 3. Yapay Zeka (OpenAI) İstemcisi
from app.clients.openai_client import OpenAIClient


def run_test_search():
    # Varsayılan test araması (Proje konunuza göre değiştirebilirsiniz)
    query = "yedekleme sistemleri"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    print(f"[SEARCH] Aranacak ifade: '{query}'")
    print("[SEARCH] Milvus istemcisi başlatılıyor ve bağlanıyor...")
    sys.stdout.flush()

    try:
        client = get_milvus_client()

        if not client.has_collection(COLLECTION_NAME):
            print(f"[SEARCH ERROR] Milvus koleksiyonu mevcut değil: {COLLECTION_NAME}")
            print("Lütfen önce 'python scripts/ingest.py' scriptini çalıştırın.")
            sys.exit(1)

        print("[SEARCH] OpenAI Embeddings ile arama terimi vektörleştiriliyor...")
        sys.stdout.flush()

        embeddings_model = OpenAIClient.get_embeddings()

        # Arama teriminin vektörünü üretiyoruz
        query_vector = embeddings_model.embed_query(query)

        print("[SEARCH] Milvus üzerinde anlamsal (vektörel) arama gerçekleştiriliyor...")
        sys.stdout.flush()

        results = client.search(
            collection_name=COLLECTION_NAME,
            data=[query_vector],
            limit=3,
            output_fields=["text", "page", "filename"]
        )

        if not results or len(results[0]) == 0:
            print("[SEARCH] Herhangi bir eşleşme bulunamadı.")
            return

        print(f"\n[SEARCH SUCCESS] En benzer {len(results[0])} sonuç bulundu:\n")

        for idx, res in enumerate(results[0]):
            entity = res.get("entity", {})
            distance = res.get("distance", 0.0)
            page = entity.get("page", "Bilinmiyor")
            filename = entity.get("filename", "Bilinmeyen Belge")
            text = entity.get("text", "")

            print(f"Eşleşme #{idx + 1} [Benzerlik Skoru (Cosine): {distance:.4f}] [Belge: {filename}] [Sayfa: {page}]")
            print("=" * 60)
            print(text.strip())
            print("=" * 60)
            print()

    except Exception as e:
        print(f"[SEARCH ERROR] Arama sırasında bir hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_test_search()