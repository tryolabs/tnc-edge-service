from sqlalchemy import Column, DateTime, Integer, String, text

from .base import Base


class BoatSchedule(Base):
    __tablename__ = "boatschedules"

    id = Column(Integer, primary_key=True)
    sentence = Column(String)
    datetime = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    def __str__(self) -> str:
        return (
            "BoatSchedule("
            + ", ".join(
                [
                    n + "=" + str(self.__getattribute__(n))
                    for n in [
                        "id",
                        "sentence",
                    ]
                ]
            )
            + ")"
        )
