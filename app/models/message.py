from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4
import datetime
from app.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True,
                default=lambda: str(uuid4()))
    case_id = Column(String, ForeignKey("cases.id"),
                     nullable=False)
    role = Column(String)
    # "user" | "agent1" | "agent2" | "system"
    content = Column(Text)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime,
                        default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="messages")
