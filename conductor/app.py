from flask import Flask
from flask.ext.cors import CORS
from .blueprints import datastore, apiload


def create():
    """Create application.
    """

    # Create application
    app = Flask('service', static_folder=None)
    app.config['DEBUG'] = True

    # CORS support
    CORS(app)

    # Register bluprints
    app.register_blueprint(datastore.create(), url_prefix='/datastore')
    app.register_blueprint(apiload.create(), url_prefix='/hooks/load/')

    # Return application
    return app
