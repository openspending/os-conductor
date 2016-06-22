from flask import Blueprint
from . import controllers


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('package', 'package')

    # Register routes
    blueprint.add_url_rule(
        'upload', 'load', controllers.upload, methods=['POST'])
    blueprint.add_url_rule(
        'status', 'poll', controllers.upload_status, methods=['GET'])
    blueprint.add_url_rule(
        'callback', 'callback',
        controllers.upload_status_update, methods=['GET'])

    # Return blueprint
    return blueprint
