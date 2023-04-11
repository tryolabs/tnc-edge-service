from http.client import BAD_REQUEST
from flask import Blueprint, make_response, request, g


from sqlalchemy.orm import scoped_session, sessionmaker

from model import DeckhandEvent, GpsData

blueprint = Blueprint('DeckhandApi', __name__)


# ORM Session
# orm_session = scoped_session(sessionmaker())

@blueprint.route('/', methods=['PUT'])
def event():
    session = g.get("db")
    d = request.get_json()

    r = session.query(GpsData)

    for i in r:
        print(i);
    
    return make_response(('', 200))
