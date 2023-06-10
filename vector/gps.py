from pynmeagps import NMEAReader

from model import RiskVector, Test

from sqlalchemy.orm import session
from model.gpsdata import GpsData

from model.test import T
import json
from datetime import datetime, timezone


class GpsVector():
    rv: RiskVector

    boundarysegments = []

    # tests = relationship("Test")
    def __init__(self, session: session, rv) -> None:
        self.session = session
        self.config(rv)
    
    def config(self, rv):
        self.rv = rv
        config = json.loads(rv.configblob)
        self.boundarysegments = boundingSegmentsFromVertices(config['boundary_vertices'])
        print(self.rv)
        print(self.boundarysegments)


    def execute(self, expected_timedelta, gpsDataSelect):
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

        result = Test(name="gps test from %s to %s"%(datetime_from,datetime_to), 
                      vector=self.rv, datetime_from=datetime_from, datetime_to=datetime_to)
        self.session.add(result)
        self.session.commit()
        # print(result)
        

        gpsDatas = self.session.query(GpsData).filter(GpsData.datetime > datetime_from).filter(GpsData.datetime < datetime_to)

        gpsPointsOutOfBounds = 0
        for gpsData in gpsDatas:

            nmea =  NMEAReader.parse(gpsData.sentence)
            point = (nmea.lat, nmea.lon)

            if not pointInBoundingBox(point, self.boundarysegments):
                gpsPointsOutOfBounds += 1
            
        result.score = -1.0/(gpsPointsOutOfBounds+1.0) + 1.0
        
        self.session.commit()

        return result


def boundingSegmentsFromVertices(vertices):
    ret = []
    first_bs = None
    last_bs = None
    for (x, y) in vertices:
        if first_bs is None:
            first_bs = (x, y)
        else:
            ret.append((last_bs, (x, y)))
        last_bs = (x, y)

    ret.append((last_bs, first_bs))
    return ret

def pointInBoundingBox(point, boundarysegments):
    """
    https://en.wikipedia.org/wiki/Point_in_polygon#Ray_casting_algorithm
    1. assume that (361,361) is outside of the gps fence
    1. make segment from (361,361) to gps coord
    1. check intersection for all boundary segments
    this algo is obviously fucked if the bounding box goes across the INTL Date Line, or surrounds either Pole
    """
    cnt = 0
    for seg in boundarysegments:
        if intersects( ((361.0,361.0), point), seg):
            cnt += 1
    
    return cnt % 2 == 1


def intersects(seg1, seg2):
    # slope = rise/run
    # slope = (y2-y1)/(x2-x1)
    slope1 = (seg1[1][1]-seg1[0][1])/(seg1[1][0]-seg1[0][0])
    slope2 = (seg2[1][1]-seg2[0][1])/(seg2[1][0]-seg2[0][0])

    # print("slope1", slope1, "slope2", slope2)
    if abs( slope1 - slope2 ) < 0.0001:
        # these lines are nearly parallel. parallel lines don't intersect.
        # also, this algorithm does 1/(s1-s2) later, so let's not divide by 0
        return False
    
    # run mx+b math to find the intersecting x coordinate
    # m1 * (x-x1) + y1 = m2*(x-x2) + y2
    # slope1 * (isectx - seg1[0][0]) + seg1[0][1] == slope2 * (isectx - seg2[0][0]) + seg2[0][1]
    # slope1 * isectx - slope1 * seg1[0][0] + seg1[0][1] == slope2 * isectx -  slope2 * seg2[0][0] + seg2[0][1]
    #                 + slope1 * seg1[0][0] - seg1[0][1] on both sides
    #                                                     - slope2 * isectx on both sides
    # slope1 * isectx - slope2 * isectx == slope1 * seg1[0][0] - seg1[0][1]  -  slope2 * seg2[0][0] + seg2[0][1]
    #       / (slope1 - slope2) on both sides

    isectx = (slope1 * seg1[0][0] - seg1[0][1] - slope2 * seg2[0][0] + seg2[0][1]) / (slope1 - slope2)
    # print("isectx", isectx)
    
    
    # I don't actually care what the y coordinate is. I only care if the intersection is on both lines.
    # I can find that just by comparing x boundaries
    between1 =  (seg1[0][0] >= isectx and isectx >= seg1[1][0]) or \
                (seg1[0][0] <= isectx and isectx <= seg1[1][0])
    
    between2 =  (seg2[0][0] >= isectx and isectx >= seg2[1][0]) or \
                (seg2[0][0] <= isectx and isectx <= seg2[1][0]) 
    return between1 and between2
    
if __name__ == '__main__':
    a = [
        NMEAReader.parse('$GPGGA,210230,3855.4487,N,09446.0071,W,1,07,1.1,370.5,M,-29.5,M,,*7A'),
        NMEAReader.parse('$GPGSV,2,1,08,02,74,042,45,04,18,190,36,07,67,279,42,12,29,323,36*77'),
        NMEAReader.parse('$GPGSV,2,2,08,15,30,050,47,19,09,158,,26,12,281,40,27,38,173,41*7B'),
        NMEAReader.parse('$GPRMC,210230,A,3855.4487,N,09446.0071,W,0.0,076.2,130495,003.8,E*69'),
    ]
    for i in a:
        print(i)

    print(intersects(((0,0), (10, 20)), ((0,0), (20, 10))))
    print(intersects(((0,1), (10, 20)), ((1,0), (20, 10))))
    print(intersects(((1,0), (10, 20)), ((0,1), (20, 10))))
    print(intersects(((0,0), (10, 20)), ((0,0), (-20, 10))))
    print(intersects(((0,0), (10, 20)), ((-20, 10), (0,0))))
    print(intersects(((0,1), (10, 20)), ((0,0), (-20, 10))))
    print(intersects(((0,1), (10, 20)), ((-20, 10), (0,0))))

    bv = [[36.9756611, -122.0273566],
          [36.9758839, -122.0255113],
          [36.9736554, -122.0240521],
          [36.9694039, -122.0231509],
          [36.9686324, -122.0227218],
          [36.9683924, -122.0248246],
          [36.9690267, -122.0263481],
          [36.9734497, -122.0270348]]
    bs = boundingSegmentsFromVertices(bv)
    print("segments", bs)

    # see visualization_of_gps_test.jpg to look at what this test is doing
    print("in box", pointInBoundingBox((36.970,-122.022), bs))
    print("in box", pointInBoundingBox((36.972,-122.022), bs))
    print("in box", pointInBoundingBox((36.975,-122.022), bs))
    print("in box", pointInBoundingBox((36.976,-122.022), bs))
    print("in box", pointInBoundingBox((36.970,-122.024), bs))
    print("in box", pointInBoundingBox((36.972,-122.024), bs))
    print("in box", pointInBoundingBox((36.975,-122.024), bs))
    print("in box", pointInBoundingBox((36.976,-122.024), bs))
    print("in box", pointInBoundingBox((36.970,-122.026), bs))
    print("in box", pointInBoundingBox((36.972,-122.026), bs))
    print("in box", pointInBoundingBox((36.975,-122.026), bs))
    print("in box", pointInBoundingBox((36.976,-122.026), bs))
    print("in box", pointInBoundingBox((36.970,-122.028), bs))
    print("in box", pointInBoundingBox((36.972,-122.028), bs))
    print("in box", pointInBoundingBox((36.975,-122.028), bs))
    print("in box", pointInBoundingBox((36.976,-122.028), bs))

