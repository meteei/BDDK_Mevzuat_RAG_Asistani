import logging
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.configs.config import settings  # Ayarları içeri aktardık

logger = logging.getLogger("OpenAI_Client")

def get_llm():
    logger.info("LLM modeli başlatılıyor (gpt-4o-mini)...")
    # API key otomatik olarak settings'den (veya .env'den) alınır
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=settings.OPENAI_API_KEY)

def get_embeddings():
    logger.info("Embedding modeli başlatılıyor (text-embedding-ada-002)...")
    return OpenAIEmbeddings(model="text-embedding-ada-002", api_key=settings.OPENAI_API_KEY)