
from model import RiskVector
from sqlalchemy.orm.session import Session
import json

class BaseVector():

    rv: RiskVector

    id: int

    def __init__(self, session: Session, rv) -> None:
        self.session = session
        self.rv = rv
        self.config()

    def config(self):

        config = json.loads(self.rv.configblob)
        # self.target_ips = config['target_ips']
        print(self.rv)

    def idfilter(self):
        return RiskVector.id == self.rv.id
        