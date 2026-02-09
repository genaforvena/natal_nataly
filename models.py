from sqlalchemy import Column, String, DateTime
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = "users"

    telegram_id = Column(String, primary_key=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
