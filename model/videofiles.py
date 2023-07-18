from .base import Base

from sqlalchemy import Column, Integer, String, DateTime, VARCHAR, text, PrimaryKeyConstraint

class VideoFile(Base):
    __tablename__ = 'video_files'
    
    original_path = Column(VARCHAR(), primary_key=True, autoincrement=False, nullable=False)
    last_modified = Column(DateTime(timezone=True), autoincrement=False, nullable=False)
    decrypted_path = Column(VARCHAR(), autoincrement=False, nullable=True)
    decrypted_datetime = Column(DateTime(timezone=True), autoincrement=False, nullable=True)
    stdout = Column(VARCHAR(), autoincrement=False, nullable=True)
    stderr = Column(VARCHAR(), autoincrement=False, nullable=True)
    

    def __str__(self) -> str:
         return 'VideoFile(' + ', '.join(
            [n + '='+ str(self.__getattribute__(n)) for n in [
                "original_path",
                "last_modified",
                "decrypted_path",
                "decrypted_datetime",
                "stdout",
                "stderr",
            ]]) + ')'
