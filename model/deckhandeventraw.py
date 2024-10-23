from sqlalchemy import Column, DateTime, Integer, String, text

from .base import Base


class DeckhandEventRaw(Base):
    __tablename__ = "deckhandevents"

    id = Column(Integer, primary_key=True)
    jsonblob = Column(String)
    datetime = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
