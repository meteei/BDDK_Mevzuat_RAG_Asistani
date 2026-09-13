from sqlalchemy import Column, Integer, String, Boolean
from app.configs.database import Base

class APILog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String, nullable=False)
    response = Column(String, nullable=False)
    time_taken_ms = Column(Integer, nullable=False)
    is_helpful = Column(Boolean, nullable=True)