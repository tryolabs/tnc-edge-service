
from model import RiskVector, Test

from sqlalchemy.orm.session import Session
from sqlalchemy.orm.query import Query
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
        
        q: Query[Test] = self.session.query(Test).filter(
            Test.datetime >= datetime_from,
            Test.datetime <= datetime_to,
            Test.vector_id.in_(self.observed_riskvector_ids),
            ).order_by(Test.datetime)
        
        tests: list[Test] = list(q.all())


        groups : dict[int, list[Test]] = {}
        group_scores : dict[int, int] = {}
        for test in tests:
            if test.vector_id not in groups.keys():
                groups[test.vector_id] = []
            groups[test.vector_id].append(test)


        for vector_id in groups.keys():
            group: list[Test] = groups[vector_id]
            expweighted = 0.0
            outage = 0.0
            # find all sequential outages. 
            # Determine a score based on how many and how long the outages are.
            # longer sequences have a much higher weight by cubing its length
            # divide by a constant scaling factor, then equalize to 0<x<1 with 1-1/(x+1)
            # scaling factor of 25 feels ok. solo outages add 3%. 3 outages in a row adds 50%.
            for test in group:
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
        
            group_scores[vector_id] = 1.0 - 1.0/(expweighted+1.0)
        
        result.detail = "vector_id=score: " + ", ".join([ "{}={}".format(k, i) for (k,i) in group_scores.items()])
        result.score = max(group_scores.values())

        self.session.commit()

        return result

if __name__ == '__main__':

    pass

