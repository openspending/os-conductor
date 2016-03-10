import os
from flask import Blueprint, request, url_for
from flask.ext.jsonpify import jsonpify

from . import controllers

os_conductor = os.environ.get('OS_EXTERNAL_ADDRESS')


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('authentication', 'authentication')

    # Controller Proxies
    check_controller = controllers.Check()
    callback_controller = controllers.Callback()

    def check():
        token = request.values.get('jwt')
        next = request.args.get('next', None)
        callback_url = 'http://'+os_conductor+url_for('.callback')
        return jsonpify(check_controller(token, next, callback_url))

    def callback():
        state = request.args.get('state')
        return callback_controller(state)

    # Register routes
    blueprint.add_url_rule(
        'check', 'check', check, methods=['GET'])
    blueprint.add_url_rule(
        'google_callback', 'callback', callback, methods=['GET'])

    # Return blueprint
    return blueprint
