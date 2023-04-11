
from model import RiskVector, Test

from sqlalchemy.orm import session
from model.internetdata import InternetData

import json
import subprocess

import re
import codecs

py38encodings = ['ascii', 'utf_32', 'utf_32_be', 'utf_32_le', 'utf_16', 'utf_16_be', 'utf_16_le', 'utf_7',
 'utf_8', 'utf_8_sig','big5', 'big5hkscs', 'cp037', 'cp273', 'cp424', 'cp437', 'cp500', 'cp720',
 'cp737', 'cp775', 'cp850', 'cp852', 'cp855', 'cp856', 'cp857', 'cp858', 'cp860', 'cp861', 'cp862',
 'cp863', 'cp864', 'cp865', 'cp866', 'cp869', 'cp874', 'cp875', 'cp932', 'cp949', 'cp950', 'cp1006',
 'cp1026', 'cp1125', 'cp1140', 'cp1250', 'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256',
 'cp1257', 'cp1258', 'euc_jp', 'euc_jis_2004', 'euc_jisx0213', 'euc_kr', 'gb2312', 'gbk', 'gb18030',
 'hz', 'iso2022_jp', 'iso2022_jp_1', 'iso2022_jp_2', 'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext',
 'iso2022_kr', 'latin_1', 'iso8859_2', 'iso8859_3', 'iso8859_4', 'iso8859_5', 'iso8859_6', 'iso8859_7',
 'iso8859_8', 'iso8859_9', 'iso8859_10', 'iso8859_11','iso8859_13', 'iso8859_14', 'iso8859_15',
 'iso8859_16', 'johab', 'koi8_r', 'koi8_t', 'koi8_u', 'kz1048', 'mac_cyrillic', 'mac_greek',
 'mac_iceland', 'mac_latin2', 'mac_roman', 'mac_turkish', 'ptcp154', 'shift_jis', 'shift_jis_2004',
 'shift_jisx0213', ]

print(subprocess.run("echo $SHELL", shell=True, capture_output=True))
loc_enc = subprocess.run("echo $LANG | awk '{split($0, a, \".\"); printf a[2]}'", shell=True, capture_output=True)
print(loc_enc)
def findencoding():
    for e in py38encodings:
        try:
            found = codecs.lookup(loc_enc.stdout.decode(e))
            yield found
        except GeneratorExit:
            return
        except:
            pass
    raise Exception('shell encoding not found')

shell_enc = next(findencoding()).name


# print(enc)

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


    def execute(self, dateRange):
        result = Test(name="internet test from %s to %s"%dateRange, vector=self.rv)
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
    p = subprocess.run(cmd, shell=True, capture_output=True, encoding=shell_enc)
    lines = json.dumps(p.stdout.strip().split("\n"))
    
    
    return InternetData(returncode=p.returncode, traceroute=lines)
   

def ping(ip):
    cmd = "ping -c 3 -W 5 -q %s "%(ip)
    p = subprocess.run(cmd, shell=True, capture_output=True, encoding=shell_enc)
    
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

