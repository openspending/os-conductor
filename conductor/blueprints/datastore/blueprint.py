import json

from flask import Blueprint, request, Response
from . import controllers


def create():
    """Create blueprint.
    """

    # Create instase
    blueprint = Blueprint('datastore', 'datastore')

    # Controller proxies
    authorize_controller = controllers.AuthorizeUpload()

    def authorize():
        auth_token = request.headers.get('Auth-Token')
        try:
            req_payload = json.loads(request.data.decode())
            return authorize_controller(auth_token, req_payload)
        except json.JSONDecodeError:
            return Response(status=400)

    # Register routes
    blueprint.add_url_rule(
            '/', 'authorize', authorize, methods=['POST'])

    # Return blueprint
    return blueprint
