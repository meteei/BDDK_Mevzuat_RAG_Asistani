# backend/app/services/memory.py
from langchain_community.chat_message_histories import ChatMessageHistory

# Oturumları bellekte tutacağımız sözlük
store = {}

def get_session_history(session_id: str):
    """Verilen oturum kimliğine göre sohbet geçmişini getirir veya yenisini oluşturur."""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]