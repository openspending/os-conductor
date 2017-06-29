import os

from flask import Blueprint, request, url_for, session
from flask.ext.jsonpify import jsonpify

from conductor.blueprints.user import controllers

os_conductor = os.environ.get('OS_EXTERNAL_ADDRESS')


def get_callback_url():
    return 'https://'+os_conductor+url_for('oauth.callback')


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('user', 'user')

    # Controller Proxies
    authenticate_controller = controllers.authenticate
    update_controller = controllers.update
    authorize_controller = controllers.authorize

    def authorize():
        token = request.values.get('jwt')
        service = request.values.get('service')
        return jsonpify(authorize_controller(token, service))

    def check():
        token = request.values.get('jwt')
        next_url = request.args.get('next', None)
        return jsonpify(
            authenticate_controller(token, next_url, get_callback_url())
        )

    def update():
        token = request.values.get('jwt')
        username = request.values.get('username')
        return jsonpify(update_controller(token, username))

    # Register routes
    blueprint.add_url_rule(
        'check', 'check', check, methods=['GET'])
    blueprint.add_url_rule(
        'update', 'update', update, methods=['POST'])
    blueprint.add_url_rule(
        'authorize', 'authorize', authorize, methods=['GET'])
    blueprint.add_url_rule(
        'public-key', 'public-key', controllers.public_key, methods=['GET'])
    blueprint.add_url_rule(
        'lib', 'lib', controllers.lib, methods=['GET'])

    # Return blueprint
    return blueprint


def oauth_create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('oauth', 'oauth')

    # Controller Proxies
    callback_controller = controllers.oauth_callback

    def callback():
        state = request.args.get('state')
        return callback_controller(state, get_callback_url())

    # Register routes
    blueprint.add_url_rule(
        'google_callback', 'callback', callback, methods=['GET'])

    # Return blueprint
    return blueprint
