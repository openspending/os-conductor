from flask import Flask
from flask.ext.cors import CORS
from flask.ext.session import Session

from .blueprints import datastore, package, user, search


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
    print("Creating Datastore Blueprint")
    app.register_blueprint(datastore.create(), url_prefix='/datastore/')
    print("Creating Package Blueprint")
    app.register_blueprint(package.create(), url_prefix='/package/')
    print("Creating Authentication Blueprint")
    app.register_blueprint(user.oauth_create(), url_prefix='/oauth/')
    print("Creating Users Blueprint")
    app.register_blueprint(user.create(), url_prefix='/user/')
    print("Creating Search Blueprint")
    app.register_blueprint(search.create(), url_prefix='/search/')

    # Return application
    return app
