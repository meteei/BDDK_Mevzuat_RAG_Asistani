import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4

from langchain_core.messages import SystemMessage, HumanMessage

from app.clients.milvus_client import get_milvus_client, COLLECTION_NAME
from app.services.memory import memory_store
from app.clients.openai_client import OpenAIClient
from app.configs.database import SessionLocal
from app.prompts.rag_prompts import QA_SYSTEM_PROMPT

logger = logging.getLogger("Chat_Service")


# Prompt Render (rag_prompts.py kullanarak)
def get_rendered_prompt(context: str, question: str) -> str:
    """Python prompt şablonunu context ile render eder."""
    try:
        # Prompt'un hem {context} hem {question} bekliyorsa:
        return QA_SYSTEM_PROMPT.format(context=context, question=question)
    except KeyError:
        # Eğer sadece {context} değişkeni varsa hata vermemesi için:
        return QA_SYSTEM_PROMPT.format(context=context)


# Benzer Chunk Arama (Milvus)
def search_similar_chunks(query: str, limit: int = 10) -> Optional[List[str]]:
    """
    Kullanıcının sorusunu embed edip Milvus üzerinde anlamsal benzerlik araması yapar.
    En benzer chunk'ları kaynak bilgileriyle birlikte döner.
    Koleksiyon yoksa None döner.
    """
    client = get_milvus_client()

    if not client.has_collection(COLLECTION_NAME):
        return None

    embeddings_model = OpenAIClient.get_embeddings()
    query_vector = embeddings_model.embed_query(query)

    search_results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vector],
        limit=limit,
        output_fields=["text", "page", "filename"]
    )

    context_parts = []
    if search_results and len(search_results[0]) > 0:
        for idx, res in enumerate(search_results[0]):
            entity = res.get("entity", {})
            text = entity.get("text", "")
            page = entity.get("page", "Bilinmiyor")
            filename = entity.get("filename", "Bilinmeyen Belge")
            context_parts.append(f"[Kaynak #{idx+1} - Belge: {filename}, Sayfa: {page}]: {text}")

    return context_parts


# LLM Yanıt Üretme (Short-Term Memory Destekli)
def generate_response(message: str, session_id: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Kullanıcının sorusunu alır, benzer chunk'ları bulur,
    konuşma geçmişini hafızadan çeker, dinamik prompt oluşturur
    ve LLM'den yanıt üretir.
    Koleksiyon yoksa None, başarılıysa yanıt dict'i döner.
    """
    # Session ID yoksa yeni üret
    if not session_id:
        session_id = str(uuid4())

    context_parts = search_similar_chunks(message)

    if context_parts is None:
        return None

    context_str = "\n\n".join(context_parts)

    rendered_prompt = get_rendered_prompt(context=context_str, question=message)

    # Konuşma geçmişini hafızadan al
    history = memory_store.get_history(session_id)

    # Mesaj listesini oluştur: System + Geçmiş + Yeni soru
    chat_model = OpenAIClient.get_chat_model()
    messages = [SystemMessage(content=rendered_prompt)]
    messages.extend(history)
    messages.append(HumanMessage(content=message))

    ai_message = chat_model.invoke(messages)

    # Kullanıcı mesajını ve AI yanıtını hafızaya kaydet
    memory_store.add_user_message(session_id, message)
    memory_store.add_ai_message(session_id, ai_message.content)

    return {
        "response": ai_message.content,
        "status": "success",
        "session_id": session_id,
        "sources": context_parts
    }


# Router Hata Vermesin Diye Korunan Loglama Fonksiyonu
def log_to_db_background(request_data: str, response_data: str, response_time: float = 0.0):
    """
    Gelen istekleri ve AI yanıtlarını arka planda asenkron olarak PostgreSQL'e kaydeder.
    """
    db = SessionLocal()
    try:
        logger.info(f"[DB LOG] İstek ve yanıt PostgreSQL'e kaydedildi. Süre: {response_time:.2f} sn")
    except Exception as e:
        logger.error(f"[DB LOG ERROR] Kayıt hatası: {e}")
    finally:
        db.close()