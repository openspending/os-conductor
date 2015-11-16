from flask import Blueprint
from . import controllers


# Create blueprint
blueprint = Blueprint('datastore', 'datastore')


# Register routes
blueprint.add_url_rule(
        '/', 'authorize', controllers.Authorize(), methods=['POST'])
