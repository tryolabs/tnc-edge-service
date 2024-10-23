import json
from http.client import BAD_REQUEST

from flask import Blueprint, g, make_response, request
from sqlalchemy.orm import scoped_session, sessionmaker

from db import db
from model import DeckhandEventRaw

blueprint = Blueprint("DeckhandApi", __name__)


# ORM Session
# orm_session = scoped_session(sessionmaker())


@blueprint.route("/", methods=["PUT", "POST"])
def event():
    d = request.get_json()

    event = DeckhandEventRaw()
    event.jsonblob = json.dumps(d)
    db.session.add(event)
    db.session.commit()

    return make_response(("", 200))
