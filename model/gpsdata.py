from .base import Base

from sqlalchemy import Column, Integer, String, DateTime, text

class GpsData(Base):
    __tablename__ = 'gpsdata'

    id = Column(Integer, primary_key=True)
    sentence = Column(String)
    datetime = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    def __str__(self) -> str:
         return 'GpsData(' + ', '.join(
            [n + '='+ str(self.__getattribute__(n)) for n in [
                'id',
                'sentence',
            ]]) + ')'
example_gps_data = '''
$ cat /mnt/thalos/brancol/export_gps/brancol_20230601_145918.txt 
+47.7411535°,-3.4073535° edge@edge1:~$ 
edge@edge1:~$ cat /mnt/thalos/brancol/export_gps/brancol_20230601_145918.txt | xxd
00000000: 2b34 372e 3734 3131 3533 35c2 b02c 2d33  +47.7411535..,-3
00000010: 2e34 3037 3335 3335 c2b0 20              .4073535.. 
'''
