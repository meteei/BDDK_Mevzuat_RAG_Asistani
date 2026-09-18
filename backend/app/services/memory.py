# backend/app/services/memory.py

"""
In-Memory Chat Short-Term Memory

Session bazlı konuşma geçmişini RAM'de tutan modül.
Her session için son N mesajı (varsayılan 10 = 5 tur) saklar.
Sunucu restart olursa hafıza sıfırlanır.
"""

import threading
from collections import deque
from typing import List, Optional

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class ChatMemoryStore:
    """
    Thread-safe, session bazlı konuşma hafızası.

    Her session_id için sabit uzunlukta bir deque tutar.
    maxlen aşıldığında en eski mesajlar otomatik düşer.
    """

    def __init__(self, max_messages_per_session: int = 10):
        """
        Args:
            max_messages_per_session: Her session için tutulacak maksimum mesaj sayısı.
                                      10 = son 5 kullanıcı + 5 AI yanıtı.
        """
        self._store: dict[str, deque] = {}
        self._lock = threading.Lock()
        self._max_messages = max_messages_per_session

    def add_user_message(self, session_id: str, content: str) -> None:
        """Kullanıcı mesajını session geçmişine ekler."""
        self._add_message(session_id, HumanMessage(content=content))

    def add_ai_message(self, session_id: str, content: str) -> None:
        """AI yanıtını session geçmişine ekler."""
        self._add_message(session_id, AIMessage(content=content))

    def get_history(self, session_id: str) -> List[BaseMessage]:
        """
        Session'a ait konuşma geçmişini LangChain mesaj listesi olarak döner.
        Session bulunamazsa boş liste döner.
        """
        with self._lock:
            if session_id not in self._store:
                return []
            return list(self._store[session_id])

    def clear(self, session_id: str) -> None:
        """Belirtilen session'ın hafızasını temizler."""
        with self._lock:
            self._store.pop(session_id, None)

    def _add_message(self, session_id: str, message: BaseMessage) -> None:
        """Dahili mesaj ekleme metodu (thread-safe)."""
        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = deque(maxlen=self._max_messages)
            self._store[session_id].append(message)


# Singleton instance — tüm uygulama boyunca aynı store kullanılır
memory_store = ChatMemoryStore()