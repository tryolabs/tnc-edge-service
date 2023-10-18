
from model import RiskVector, Test

from sqlalchemy.orm import session
from model.internetdata import InternetData

import json
import subprocess

import re
import codecs

from datetime import datetime, timedelta, timezone

class InternetVector():
    target_ips = []

    # tests = relationship("Test")
    def __init__(self, session: session, rv) -> None:
        self.session = session
        self.config(rv)
    
    def config(self, rv):
        self.rv = rv
        config = json.loads(rv.configblob)
        self.target_ips: list[str] = config['target_ips']
        self.run_traceroute: bool = config['run_traceroute'] 
        print(self.rv)
        print(self.target_ips)


    
    def execute(self, expected_timedelta: timedelta):
        datetime_to = datetime.now(tz=timezone.utc)
        datetime_from = datetime_to - expected_timedelta

        last = self.session.query(Test)\
            .where(Test.vector_id == self.rv.id, Test.datetime_to < datetime_to)\
            .order_by(Test.datetime_to.desc())\
            .limit(1).all()
        
        result = Test(name="internet test at %s"%(datetime_to.strftime('%Y-%m-%d %H:%M:%SZ')), vector=self.rv)
        self.session.add(result)
        self.session.commit()
        # print(result)
        
        datas = []

        for ip in self.target_ips:
            if self.run_traceroute:
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

