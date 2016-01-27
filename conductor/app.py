from flask import Flask
from flask.ext.cors import CORS
from flask.ext.session import Session

from .blueprints import datastore, apiload, authentication, authorization


def create():
    """Create application.
    """

    # Create application
    app = Flask('service', static_folder=None)
    app.config['DEBUG'] = True

    # CORS support
    CORS(app)

    # Session
    sess = Session()
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = 'openspending rocks'
    sess.init_app(app)

    # Register blueprints
    app.register_blueprint(datastore.create(), url_prefix='/datastore')
    app.register_blueprint(apiload.create(), url_prefix='/hooks/load/')
    app.register_blueprint(authentication.create(), url_prefix='/oauth/')
    app.register_blueprint(authorization.create(), url_prefix='/permit/')

    # Return application
    return app
