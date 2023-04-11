
from model import RiskVector
from sqlalchemy.orm.session import Session
import json

class BaseVector():
    """
    this class is not used. maybe someday it will contain base values for all vectors, but not today.
    I don't trust that sqlalchemy's declarative orm features will work with parent classes like this.
    """

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
        