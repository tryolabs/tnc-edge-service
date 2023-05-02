from http.client import BAD_REQUEST
from flask import Blueprint, make_response, request, g


from sqlalchemy.orm import scoped_session, sessionmaker

from model import DeckhandEvent

import json

from db import db

blueprint = Blueprint('DeckhandApi', __name__)


# ORM Session
# orm_session = scoped_session(sessionmaker())

@blueprint.route('/', methods=['PUT', 'POST'])
def event():
    s = db._make_scoped_session
    d = request.get_json()

    event = DeckhandEvent()
    # event.id=1
    event.jsonblob = json.dumps(d)
    db.session.add(event)
    db.session.commit()
    # r = db.session.query()

    # for i in r:
    #     print(i);
    
    return make_response(('', 200))
