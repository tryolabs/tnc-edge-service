from datetime import datetime, timedelta, timezone
from nmeasim.models import GpsReceiver
import time
import requests
from random import random

gps = GpsReceiver(
    date_time=datetime.now(tz=timezone.utc),
    output=('RMC',)
)
while(True):
    
    gps.date_time = datetime.now() 
    gps.lat = 36.97471678054289 + random()*0.0002
    gps.lon = -122.02610556256218  + random()*0.0002
    
    resp = requests.post('http://localhost:50000/admin/gpsdata/new/', data={
        'sentence': gps.get_output()[0],
        'datetime': '',
    }, headers={"Accept-Encoding":None})
    print(resp, resp.headers)

    time.sleep(5)

