from sqlalchemy import REAL, Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import relationship

from .base import Base
from .videofiles import VideoFile


class AifishData(Base):
    __tablename__ = "aifishdata"

    id = Column(Integer, primary_key=True)
    video_uri = Column(String, ForeignKey("video_files.decrypted_path"), unique=True)
    video_file = relationship(VideoFile)
    processing_uri = Column(String)
    output_uri = Column(String)
    datetime = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    count = Column(Integer)
    runtimems = Column(REAL)
    detection_confidence = Column(REAL)
    status = Column(String)

    def __str__(self) -> str:
        return (
            "AifishData("
            + ", ".join(
                [
                    n + "=" + str(self.__getattribute__(n))
                    for n in [
                        "id",
                        "video_uri",
                        # 'video_file',
                        "processing_uri",
                        "output_uri",
                        "datetime",
                        "count",
                        "runtimems",
                        "detection_confidence",
                        "status",
                    ]
                ]
            )
            + ")"
        )
