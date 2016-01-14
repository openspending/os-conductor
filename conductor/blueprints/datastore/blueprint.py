from flask import Blueprint
from . import controllers


def create():
    """Create blueprint.
    """

    # Create instase
    blueprint = Blueprint('datastore', 'datastore')

    # Register routes
    blueprint.add_url_rule(
            '/', 'authorize', controllers.Authorize(), methods=['POST'])

    # Return blueprint
    return blueprint
