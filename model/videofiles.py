from .base import Base

from sqlalchemy import Column, Integer, String, DateTime, VARCHAR, text, PrimaryKeyConstraint
# from sqlalchemy.orm import relationship

class VideoFile(Base):
    __tablename__ = 'video_files'
    
    original_path = Column(VARCHAR(), primary_key=True, autoincrement=False, nullable=False)
    last_modified = Column(DateTime(timezone=True), autoincrement=False, nullable=False)
    start_datetime = Column(DateTime(timezone=True), autoincrement=False, nullable=False)
    decrypted_path = Column(VARCHAR(), autoincrement=False, nullable=True)
    decrypted_datetime = Column(DateTime(timezone=True), autoincrement=False, nullable=True)
    stdout = Column(VARCHAR(), autoincrement=False, nullable=True)
    stderr = Column(VARCHAR(), autoincrement=False, nullable=True)
    cam_name = Column(VARCHAR(), nullable=True)
    
    # ondeckdata = relationship("OndeckData", back_populates="video_file")

    def __str__(self) -> str:
         return 'VideoFile(' + ', '.join(
            [n + '='+ str(self.__getattribute__(n)) for n in [
                "original_path",
                "last_modified",
                "start_datetime",
                "decrypted_path",
                "decrypted_datetime",
                "stdout",
                "stderr",
                "cam_name",
            ]]) + ')'
