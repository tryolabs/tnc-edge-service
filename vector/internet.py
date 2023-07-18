
from model import RiskVector, Test

from sqlalchemy.orm import session
from model.internetdata import InternetData

import json
import subprocess

import re
import codecs

from datetime import datetime, timezone

class InternetVector():
    target_ips = []

    # tests = relationship("Test")
    def __init__(self, session: session, rv) -> None:
        self.session = session
        self.config(rv)
    
    def config(self, rv):
        self.rv = rv
        config = json.loads(rv.configblob)
        self.target_ips = config['target_ips']
        print(self.rv)
        print(self.target_ips)


    
    def execute(self, expected_timedelta):
        datetime_to = datetime.now(tz=timezone.utc)
        datetime_from = datetime_to - expected_timedelta
        last = self.session.query(Test)\
            .where(Test.vector_id == self.rv.id, Test.datetime_to < datetime_to)\
            .order_by(Test.datetime_to.desc())\
            .limit(1).all()
        
        if len(list(last)) :
            last_datetime = last[0].datetime_to
            if datetime_to - last_datetime < expected_timedelta * 2:
                datetime_from = last_datetime
                print("found previous run, referencing datetime_to")
            else:
                print("found previous run, datetime_to is too old")
        else:
            print("no previous run found, using expected_timedelta")
        
        result = Test(name="internet test from %s to %s"%(datetime_from,datetime_to), vector=self.rv)
        self.session.add(result)
        self.session.commit()
        # print(result)
        
        datas = []

        for ip in self.target_ips:
            data = traceroute(ip)
            datas.append(data)
            self.session.add(data)
            self.session.commit()
            
            data = ping(ip)
            datas.append(data)
            self.session.add(data)
            self.session.commit()
        
        f = filter(lambda data: data.returncode != 0 or data.packetloss and data.packetloss > 33.4 , datas)
        result.score = -1.0/(len(list(f))+1.0) + 1.0
        
        self.session.commit()

        return result

def traceroute(ip):
    cmd = "traceroute -m 12 %s | grep -E '^\s*[0-9][0-9]*\s*' | grep -v '\* \* \*' | awk '{{print $2 \" \" $3}}' "%(ip)
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    lines = json.dumps(p.stdout.strip().split("\n"))
    
    
    return InternetData(returncode=p.returncode, traceroute=lines)
   

def ping(ip):
    cmd = "ping -c 3 -W 5 -q %s "%(ip)
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    data = InternetData(returncode=p.returncode)
    for line in p.stdout.strip().split("\n"):
        # print(line)
        m = re.search('([\d\.]+)\% packet loss', line)
        if m:
            # print("loss", m[1])
            data.packetloss = float(m[1])
            continue
        m = re.search('min/avg/.*= [\d\.]+/([\d\.]+)/', line)
        if m:
            # print("ping", m[1])
            data.ping = float(m[1])
            continue

    return data
   

if __name__ == '__main__':

    
    print(traceroute('1.1.1.1'))
    print(ping('1.1.1.1'))

