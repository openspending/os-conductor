from flask import Blueprint, request
from flask.ext.jsonpify import jsonpify
from . import controllers


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('authorization', 'authorization')

    # Controller Proxies
    check_controller = controllers.Check()

    def check():
        token = request.values.get('jwt')
        service = request.values.get('service')
        return jsonpify(check_controller(token, service))

    # Register routes
    blueprint.add_url_rule(
        'check', 'check', check, methods=['GET'])
    blueprint.add_url_rule(
        'public-key', 'public-key', controllers.PublicKey(), methods=['GET'])
    blueprint.add_url_rule(
        'lib', 'lib', controllers.Lib(), methods=['GET'])

    # Return blueprint
    return blueprint
