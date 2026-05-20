from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from uuid import uuid4
import datetime
from app.database import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True,
                default=lambda: str(uuid4()))
    user_id = Column(Uuid, ForeignKey("users.id"),
                     nullable=False)
    title = Column(String, nullable=True)
    issue_type = Column(String, nullable=True)
    status = Column(String, default="draft")
    # status flow: draft → analysed → document_ready → filed
    legal_brief = Column(JSON, nullable=True)
    action_log = Column(JSON, default=list)
    case_ref = Column(String, nullable=True)
    created_at = Column(DateTime,
                        default=datetime.datetime.utcnow)
    updated_at = Column(DateTime,
                        default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    messages = relationship("Message", back_populates="case")
    documents = relationship("Document", back_populates="case")
