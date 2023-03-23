from .base import Base

from sqlalchemy import Column, Integer, String, DateTime, text

class FishAiData(Base):
    __tablename__ = 'fishaidata'

    id = Column(Integer, primary_key=True)
    video_uri = Column(String)
    cocoannotations_uri = Column(String)
    datetime = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    def __str__(self) -> str:
         return 'FishAiData(' + ', '.join(
            [n + '='+ str(self.__getattribute__(n)) for n in [
                'id',
                'video_uri',
                'cocoannotations_uri',
                'datetime',
            ]]) + ')'
