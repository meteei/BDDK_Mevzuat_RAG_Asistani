# backend/app/schemas/schemas.py

from typing import Optional, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ..., 
        description="Kullanıcının BDDK regülasyonları ve bankacılık mevzuatı ile ilgili sorusu", 
        examples=["Birincil ve ikincil sistemler nerede bulundurulmalıdır?"]
    )
    session_id: Optional[str] = Field(
        None, 
        description="Konuşma oturum kimliği. Gönderilmezse otomatik üretilir."
    )


from typing import List, Optional
from pydantic import BaseModel, Field

class ChatResponse(BaseModel):
    response: str = Field(
        ...,
        description="Yapay zeka asistanının mevzuata dayalı denetçi tonundaki cevabı"
    )
    status: str = Field(
        "success",
        description="İşlem durumu"
    )
    session_id: str = Field(
        ...,
        description="Konuşma oturum kimliği"
    )
    sources: List[str] = Field(
        default=[],
        description="Cevabın dayandığı kaynak belge ve madde bilgileri"
    )
    log_id: Optional[int] = Field(
        default=0,
        description="Veritabanındaki sohbet logunun benzersiz kimliği (Geri bildirim için gereklidir)"
    )