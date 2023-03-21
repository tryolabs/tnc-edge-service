from http.client import BAD_REQUEST
from flask import Blueprint, make_response, request



from model import DeckhandEvent

blueprint = Blueprint('DeckhandApi', __name__)

@blueprint.route('/', methods=['PUT'])
def event():

    d = request.get_json()
    
    return make_response(('', 200))