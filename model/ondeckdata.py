from .base import Base
from .videofiles import VideoFile

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, text
from sqlalchemy.orm import relationship

class OndeckData(Base):
    __tablename__ = 'ondeckdata'

    id = Column(Integer, primary_key=True)
    video_uri = Column(String, ForeignKey("video_files.decrypted_path"))
    video_file = relationship(VideoFile)
    cocoannotations_uri = Column(String)
    datetime = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    def __str__(self) -> str:
         return 'OndeckData(' + ', '.join(
            [n + '='+ str(self.__getattribute__(n)) for n in [
                'id',
                'video_uri',
                'cocoannotations_uri',
                'datetime',
            ]]) + ')'

