
from model import RiskVector, Test

from sqlalchemy.orm.session import Session
from model import Test
from vector import InternetVector

import json

from datetime import datetime, timedelta, timezone



class EquipmentOutageAggVector():
    rv: RiskVector
    sessin: Session

    def __init__(self, session: Session, rv) -> None:
        self.session = session
        self.config(rv)
    
    def config(self, rv):
        self.rv = rv
        config = json.loads(rv.configblob)
        self.observed_riskvector_ids = config['observed_riskvector_ids']
        print(self.rv)


    def execute(self, expected_timedelta: timedelta):

        datetime_to = datetime.now(tz=timezone.utc)
        datetime_from = datetime_to - expected_timedelta

        result = Test(name="equipment outage aggregator from %s to %s"%(datetime_from, datetime_to), vector=self.rv)
        self.session.add(result)
        self.session.commit()
        # print(result)
        
        tests = self.session.query(Test).filter(
            Test.datetime >= datetime_from,
            Test.datetime <= datetime_to,
            Test.vector_id.in_(self.observed_riskvector_ids),
            ).order_by(Test.datetime)
        
        expweighted = 0.0
        outage = 0.0

        # find all sequential outages. 
        # Determine a score based on how many and how long the outages are.
        # longer sequences have a much higher weight by cubing its length
        # divide by a constant scaling factor, then equalize to 0<x<1 with 1-1/(x+1)
        for test in tests.all():
            print("expweighted: %s outage: %d "%(expweighted,outage))
            if test.score > 0.0:
                outage += 1
            else:
                if outage > 0:
                    # this is the end of a sequence, cube its length
                    expweighted += outage * outage * outage / 200.0
                outage = 0
        
        if outage > 0:
            expweighted += outage * outage * outage / 200.0
        
        print("expweighted: %s outage: %d "%(expweighted,outage))
        
        result.score = 1.0 - 1.0/(expweighted+1.0)
        
        self.session.commit()

        return result



if __name__ == '__main__':

    pass
