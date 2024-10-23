import json
import os
from datetime import datetime, timedelta, timezone

from dateutil.parser import isoparse
from sqlalchemy.orm import session

from model import RiskVector, Test
from model.aifishdata import AifishData


class FishAiEventsComeInFourHourBurstsVector:
    rv: RiskVector

    # tests = relationship("Test")
    def __init__(self, s: session, rv) -> None:
        self.session = s
        self.config(rv)

    def config(self, rv):
        self.rv = rv
        confblob = json.loads(rv.configblob)
        self.target_category_id = confblob["target_category_id"]
        self.video_fps = confblob["video_fps"]
        self.event_grouping_timedelta = timedelta(
            seconds=confblob["event_grouping_timedelta_seconds"]
        )
        self.expected_gap_between_groups = timedelta(
            seconds=confblob["expected_gap_between_groups_seconds"]
        )
        print(self.rv)
        print(confblob)

    def execute(self, expected_timedelta):
        datetime_to = datetime.now(tz=timezone.utc)
        datetime_from = datetime_to - expected_timedelta

        fishAiDatas = (
            self.session.query(AifishData)
            .filter(AifishData.datetime > datetime_from)
            .filter(AifishData.datetime < datetime_to)
        )

        scores_per_file = []

        for fishAiData in fishAiDatas:
            cocofilename = fishAiData.cocoannotations_uri
            cocofilestat = os.stat(cocofilename)
            with open(cocofilename) as f:
                raw = json.load(f)
                starttime = isoparse(raw["info"]["date_created"])
                endtime = fishAiData.datetime
                annos = raw["annotations"]
                tracks_set = {}
                for anno in annos:
                    if not anno["category_id"] == self.target_category_id:
                        continue
                    track_id = anno["attributes"]["track_id"]
                    if track_id not in tracks_set:
                        tracks_set[track_id] = {
                            "track_id": track_id,
                            "mintime": datetime(9999, 12, 31, 23, 59, 59),
                            "maxtime": datetime.fromtimestamp(0),
                        }
                    track = tracks_set[track_id]
                    frameTime = frameToTime(starttime, self.video_fps, anno["image_id"])
                    if frameTime < track["mintime"]:
                        track["mintime"] = frameTime
                    if frameTime > track["maxtime"]:
                        track["maxtime"] = frameTime
                tracksByStartTime = list(tracks_set.values())
                tracksByStartTime.sort(key=lambda x: x["mintime"])

                # greedy left-to-right grouping algorithm:
                groups = []
                for t in tracksByStartTime:
                    if len(groups) == 0:
                        groups.append(dict(t))
                        continue
                    if groups[-1]["maxtime"] + self.event_grouping_timedelta >= t["mintime"]:
                        latertime = (
                            t["maxtime"]
                            if t["maxtime"] > groups[-1]["maxtime"]
                            else groups[-1]["maxtime"]
                        )
                        groups[-1]["maxtime"] = latertime
                    else:
                        groups.append(dict(t))

                score = 0
                if len(groups) > 1:
                    mingap = None
                    for i in range(len(groups) - 1):
                        curr_gap = groups[i + 1]["mintime"] - groups[i]["maxtime"]
                        mingap = curr_gap if mingap == None or curr_gap < mingap else mingap

                    if mingap < self.expected_gap_between_groups:
                        score = (
                            1.0
                            / (
                                (10.0 / self.expected_gap_between_groups.seconds)
                                * (mingap.seconds - self.expected_gap_between_groups.seconds)
                                - 1.0
                            )
                            + 1.0
                        )
                scores_per_file.append(score)

        if len(scores_per_file) > 0:
            t = Test(
                name="Higher score from a short gap between ai detection events. Test bounds from %s to %s"
                % (datetime_from, datetime_to),
                vector=self.rv,
                score=sum(scores_per_file),
            )
            self.session.add(t)

            self.session.commit()


def frameToTime(starttime, video_fps, frameno):
    return starttime + timedelta(seconds=float(frameno) / video_fps)


# test by running directly with `python3 -m vector.fname`
if __name__ == "__main__":
    """
    Test
    """

    import sqlite3

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from model import Base as ModelBase

    engine = create_engine("sqlite:///db.db", echo=True)
    SessionMaker = sessionmaker(engine)

    ModelBase.metadata.create_all(engine)

    with sqlite3.connect("db.db") as conn:
        with SessionMaker() as s:
            print("start of cron")
            q = s.query(RiskVector).filter(
                RiskVector.name == FishAiEventsComeInFourHourBurstsVector.__name__
            )

            for rv in q.all():
                f = FishAiEventsComeInFourHourBurstsVector(s, rv)
                f.execute((datetime.now() - timedelta(weeks=500), datetime.now()))
