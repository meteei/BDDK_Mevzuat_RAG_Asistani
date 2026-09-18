# backend/app/models/models.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.configs.database import Base


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_body = Column(Text, nullable=False)
    response_body = Column(Text, nullable=False)
    duration = Column(Integer, nullable=False)  # Veya float
    log_level = Column(String(50), default="INFO", nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)
    is_helpful = Column(Boolean, nullable=True)  # İsteğe bağlı geri bildirim alanı

    def __repr__(self):
        return f"<ChatLog id={self.id} duration={self.duration}s level={self.log_level}>"


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(String(50), default="processing", nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<UploadedDocument id={self.id} filename={self.filename} status={self.status}>"