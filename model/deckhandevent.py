
from .base import Base

from sqlalchemy import Column, Integer, String, DateTime, text


class DeckhandEvent(Base):

    __tablename__ = 'deckhandevents'

    id = Column(Integer, primary_key=True)
    jsonblob = Column(String)
    datetime = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    
    