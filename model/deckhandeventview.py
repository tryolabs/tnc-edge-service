
from .base import Base

from sqlalchemy import Column, Integer, String, DateTime, text


class DeckhandEventView(Base):

    __tablename__ = 'deckhandevents_mostrecentlonglineevent_jsonextracted'

    id = Column(Integer, primary_key=True)
    # jsonblob = Column(String)
    datetime = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    
    bycatchcount = Column(Integer)
    catchcount = Column(Integer)
    systemstartsetdatetime = Column(DateTime(timezone=True))
    systemstartsetlatitude = Column(Integer)
    systemstartsetlongitude = Column(Integer)
    systemendsetdatetime = Column(DateTime(timezone=True))
    systemendsetlatitude = Column(Integer)
    systemendsetlongitude = Column(Integer)
    systemstarthauldatetime = Column(DateTime(timezone=True))
    systemstarthaullatitude = Column(Integer)
    systemstarthaullongitude = Column(Integer)
    systemendhauldatetime = Column(DateTime(timezone=True))
    systemendhaullatitude = Column(Integer)
    systemendhaullongitude = Column(Integer)
    
 
if __name__ == '__main__':
    pass