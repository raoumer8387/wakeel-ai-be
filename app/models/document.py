from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4
import datetime
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True,
                default=lambda: str(uuid4()))
    case_id = Column(String, ForeignKey("cases.id"),
                     nullable=False)
    type = Column(String)
    file_path = Column(String)
    generated_by = Column(String,
                          default="document_specialist_agent")
    created_at = Column(DateTime,
                        default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="documents")
