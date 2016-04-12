from flask import Blueprint, abort, request
from flask.ext.jsonpify import jsonpify
from . import controllers


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('search', 'search')

    # Controller Proxies
    search_controller = controllers.Search()

    def search(kind):
        ret = search_controller(kind, request.args)
        if ret is None:
            abort(400)
        return jsonpify(ret)

    # Register routes
    blueprint.add_url_rule(
        '<kind>', 'search', search, methods=['GET'])

    # Return blueprint
    return blueprint
