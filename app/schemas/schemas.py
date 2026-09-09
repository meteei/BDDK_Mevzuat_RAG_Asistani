from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # Frontend göndermezse None olacak, Backend kendisi benzersiz UUID üretecek.

class QueryResponse(BaseModel):
    log_id: int
    query: str
    answer: str
    time_taken_ms: int
    sources: List[str] = []
    session_id: str  # Kullanılan oturum kimliğini arayüze geri döndürmek için eklendi.