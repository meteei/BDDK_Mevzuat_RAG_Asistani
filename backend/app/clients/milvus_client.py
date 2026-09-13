import logging
from langchain_milvus import Milvus
from app.configs.config import settings  # Ayarları içeri aktardık

logger = logging.getLogger("Milvus_Client")

def get_vector_store(embeddings):
    logger.info(f"Milvus veritabanına bağlanılıyor ({settings.MILVUS_HOST}:{settings.MILVUS_PORT})...")
    vector_store = Milvus(
        embedding_function=embeddings,
        collection_name="bddk_regulations",
        connection_args={"host": settings.MILVUS_HOST, "port": settings.MILVUS_PORT},
    )
    return vector_store