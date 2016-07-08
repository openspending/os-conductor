import jwt
from flask import Blueprint, abort, request
from flask.ext.jsonpify import jsonpify

from conductor.blueprints.user.controllers import PRIVATE_KEY
from . import controllers


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('search', 'search')

    # Controller Proxies
    search_controller = controllers.search

    def search(kind):
        token = request.values.get('jwt')
        userid = None
        try:
            if token is not None:
                token = jwt.decode(token, PRIVATE_KEY)
                userid = token.get('userid')
        except jwt.InvalidTokenError:
            pass
        ret = search_controller(kind, userid, request.args)
        if ret is None:
            abort(400)
        return jsonpify(ret)

    # Register routes
    blueprint.add_url_rule(
        '<kind>', 'search', search, methods=['GET'])

    # Return blueprint
    return blueprint
