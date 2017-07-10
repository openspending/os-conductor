import os

from flask import Blueprint, request, url_for, session
from flask import redirect
from flask_jsonpify import jsonpify

from .controllers import authenticate, authorize, update, oauth_callback, setup_oauth_apps
from .models import setup_engine
from .credentials import \
    google_key, google_secret, \
    github_key, github_secret, \
    private_key, public_key, \
    db_connection_string


def make_blueprint(external_address):
    """Create blueprint.
    """

    setup_oauth_apps(google_key=google_key,
                     google_secret=google_secret,
                     github_key=github_key,
                     github_secret=github_secret)
    setup_engine(db_connection_string)

    # Create instance
    blueprint = Blueprint('auth', 'auth')

    # Controller Proxies
    authenticate_controller = authenticate
    update_controller = update
    authorize_controller = authorize
    oauth_callback_controller = oauth_callback

    def callback_url():
        return 'https://'+external_address+url_for('auth.oauth_callback')

    def authorize_():
        token = request.headers.get('auth-token') or request.values.get('jwt')
        service = request.values.get('service')
        return jsonpify(authorize_controller(token, service, private_key))

    def check_():
        token = request.headers.get('auth-token') or request.values.get('jwt')
        next_url = request.args.get('next', None)
        return jsonpify(authenticate_controller(token, next_url, callback_url(), private_key))

    def update_():
        token = request.headers.get('auth-token') or request.values.get('jwt')
        username = request.values.get('username')
        return jsonpify(update_controller(token, username, private_key))

    def oauth_callback_():
        state = request.args.get('state')

        def set_session(k, v):
            session[k] = v

        return redirect(oauth_callback_controller(state, callback_url(), private_key, set_session))

    def public_key_():
        return public_key

    # Register routes
    blueprint.add_url_rule(
        'check', 'check', check_, methods=['GET'])
    blueprint.add_url_rule(
        'update', 'update', update_, methods=['POST'])
    blueprint.add_url_rule(
        'authorize', 'authorize', authorize_, methods=['GET'])
    blueprint.add_url_rule(
        'public-key', 'public-key', public_key_, methods=['GET'])
    blueprint.add_url_rule(
        'oauth_callback', 'oauth_callback', oauth_callback_, methods=['GET'])

    # Return blueprint
    return blueprint
