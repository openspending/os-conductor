import sys

from flask import Flask
from flask.ext.cors import CORS
from flask.ext.session import Session

from .blueprints import datastore, apiload, authentication, authorization


def create():
    """Create application.
    """

    print('SSS 1')
    sys.stdout.flush()
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

    print('SSS 2')
    sys.stdout.flush()

    # Register blueprints
    print('SSS 3')
    sys.stdout.flush()
    app.register_blueprint(datastore.create(), url_prefix='/datastore')

    print('SSS 4')
    sys.stdout.flush()
    app.register_blueprint(apiload.create(), url_prefix='/hooks/load/')

    print('SSS 5')
    sys.stdout.flush()
    app.register_blueprint(authentication.create(), url_prefix='/oauth/')

    print('SSS 6')
    sys.stdout.flush()
    app.register_blueprint(authorization.create(), url_prefix='/permit/')

    print('SSS 7')
    sys.stdout.flush()

    # Return application
    return app
