from flask import Blueprint
from . import controllers


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('authorization', 'authorization')

    # Register routes
    blueprint.add_url_rule(
        'check', 'check', controllers.Check(), methods=['GET'])
    blueprint.add_url_rule(
        'public-key', 'public-key', controllers.PublicKey(), methods=['GET'])
    blueprint.add_url_rule(
        'sample/<path:path>', 'sample', controllers.Sample(), methods=['GET'])
    blueprint.add_url_rule(
        'sample', 'service', controllers.SampleService(), methods=['POST'])

    # Return blueprint
    return blueprint
