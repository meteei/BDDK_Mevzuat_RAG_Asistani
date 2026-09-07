from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    query: str
    session_id: str = "default_session" # Hangi kullanıcının hafızası olduğunu tutar

class QueryResponse(BaseModel):
    log_id: int  # YENİ EKLENEN SATIR
    query: str
    answer: str
    time_taken_ms: int
    sources: List[str] = []