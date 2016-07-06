import json

from flask import Blueprint, request, Response
from . import controllers


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('datastore', 'datastore')

    # Controller proxies
    def authorize():
        auth_token = request.headers.get('Auth-Token')
        if auth_token is None:
            auth_token = request.values.get('jwt')
        try:
            req_payload = json.loads(request.data.decode())
            return controllers.authorize(controllers.S3Connection(),
                                         auth_token, req_payload)
        except json.JSONDecodeError:
            return Response(status=400)

    # Register routes
    blueprint.add_url_rule(
            '/', 'authorize', authorize, methods=['POST'])

    # Return blueprint
    return blueprint
