from .base import Base
from .videofiles import VideoFile

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, text, REAL, ARRAY
from sqlalchemy.orm import relationship

class Track(Base):
    __tablename__ = 'tracks'

    id = Column(Integer, primary_key=True)
    video_uri = Column(String)
    # video_uri = Column(String, ForeignKey("video_files.decrypted_path"))
    # video_file = relationship(VideoFile)
    cocoannotations_uri = Column(String)
    # cocoannotations_uri = Column(String, ForeignKey("ondeckdata.cocoannotations_uri"))
    # ondeckdata = relationship(OndeckData)
    track_id = Column(Integer)
    first_framenum = Column(Integer)
    last_framenum = Column(Integer)
    confidences = Column(ARRAY(REAL))


    datetime = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    # detection_confidence = Column(REAL)

    def __str__(self) -> str:
         return 'Track(' + ', '.join(
            [n + '='+ str(self.__getattribute__(n)) for n in [
                'id',
                
            ]]) + ')'
