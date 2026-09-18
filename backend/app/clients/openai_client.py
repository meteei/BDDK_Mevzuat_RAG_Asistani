import logging
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.configs.config import settings

logger = logging.getLogger("OpenAI_Client")

class OpenAIClient:
    """
    OpenAI Embedding ve Chat model istemcisi.
    Lazy singleton deseni ile modelleri sadece ilk kullanımda başlatır.

    chat_service, document_service ve scriptler
    tarafından ortaklaşa kullanılır.
    """

    _embeddings_instance = None
    _chat_instance = None

    @classmethod
    def get_embeddings(cls) -> OpenAIEmbeddings:
        """OpenAI Embeddings modelini döner (lazy singleton)."""
        if cls._embeddings_instance is None:
            logger.info("Embedding modeli başlatılıyor (text-embedding-ada-002)...")
            cls._embeddings_instance = OpenAIEmbeddings(
                model="text-embedding-ada-002",
                api_key=settings.OPENAI_API_KEY
            )
        return cls._embeddings_instance

    @classmethod
    def get_chat_model(cls) -> ChatOpenAI:
        """OpenAI Chat modelini döner (lazy singleton)."""
        if cls._chat_instance is None:
            logger.info("LLM modeli başlatılıyor (gpt-4o-mini)...")
            cls._chat_instance = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=settings.OPENAI_API_KEY
            )
        return cls._chat_instance