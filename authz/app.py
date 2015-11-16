from flask import Flask
from flask.ext.cors import CORS
from .blueprints import datastore


def create():
    """Create application.
    """

    # Create application
    app = Flask('service', static_folder=None)

    # CORS support
    CORS(app)

    # Register bluprints
    app.register_blueprint(datastore.create(), url_prefix='/datastore')

    # Return application
    return app
