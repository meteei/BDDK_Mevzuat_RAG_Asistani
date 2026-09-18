# backend/app/clients/milvus_client.py

from pymilvus import MilvusClient, DataType
from app.configs.config import settings

# Milvus koleksiyon ismi
COLLECTION_NAME = "bddk_regulations"
VECTOR_DIMENSION = 1536


def get_milvus_client() -> MilvusClient:
    """
    Milvus istemcisini başlatır ve döner.
    """
    uri = f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}"
    return MilvusClient(uri=uri)


def create_collection_if_not_exists() -> None:
    """
    Belge metinlerinin, meta verilerinin ve vektörlerinin saklanacağı
    Milvus koleksiyonunu oluşturur ve indeks tanımlamasını yapar.
    """
    client = get_milvus_client()
    try:
        # Koleksiyon zaten varsa ve şemayı güncellemek istiyorsak,
        # eskisini silip yenisini kurmak en güvenlisidir.
        # (İsterseniz test aşamasında doğrudan drop edebilirsiniz)
        if client.has_collection(COLLECTION_NAME):
            print(f"[MILVUS] Koleksiyon '{COLLECTION_NAME}' zaten mevcut.")
            return

        schema = client.create_schema(
            auto_id=True,
            enable_dynamic_field=True,
            description="RAG Belgeleri Vektör Şeması"
        )

        # Fields (Tüm arama ve filtre alanlarını eksiksiz ekliyoruz)
        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
        schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
        schema.add_field(field_name="page", datatype=DataType.INT64)
        schema.add_field(field_name="doc_id", datatype=DataType.INT64)
        schema.add_field(field_name="filename", datatype=DataType.VARCHAR, max_length=255)
        schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=VECTOR_DIMENSION)

        # İndex ayarları
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            metric_type="COSINE",
            index_type="HNSW",
            params={"M": 16, "efConstruction": 64}
        )

        # Koleksiyonun indeksle birlikte oluşturulması
        client.create_collection(
            collection_name=COLLECTION_NAME,
            schema=schema,
            index_params=index_params
        )
        print(f"[MILVUS] Koleksiyon '{COLLECTION_NAME}' başarıyla ve tam şemayla oluşturuldu.")

    except Exception as e:
        print(f"[MILVUS] Koleksiyon oluşturulurken hata oluştu: {e}")
        raise e