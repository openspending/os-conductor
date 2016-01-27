from flask import Blueprint
from . import controllers


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('authentication', 'authentication')

    # Register routes
    blueprint.add_url_rule(
        'check', 'check', controllers.Check(), methods=['GET'])
    blueprint.add_url_rule(
        'google_callback', 'callback', controllers.Callback(), methods=['GET'])

    # Return blueprint
    return blueprint
