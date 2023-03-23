from .base import Base

from sqlalchemy import Column, Integer, String, DateTime, text

class GpsData(Base):
    __tablename__ = 'gpsdata'

    id = Column(Integer, primary_key=True)
    sentence = Column(String)
    datetime = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    def __str__(self) -> str:
         return 'GpsData(' + ', '.join(
            [n + '='+ str(self.__getattribute__(n)) for n in [
                'id',
                'sentence',
            ]]) + ')'
