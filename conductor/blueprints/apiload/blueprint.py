from flask import Blueprint
from . import controllers


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('apiload', 'apiload')

    # Register routes
    blueprint.add_url_rule(
        'api', 'load', controllers.ApiLoad(), methods=['POST'])
    blueprint.add_url_rule(
        'api', 'poll', controllers.ApiPoll(), methods=['GET'])

    # Return blueprint
    return blueprint
