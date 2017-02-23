import os

from flask import Flask
from flask.ext.cors import CORS
from flask.ext.session import Session
from raven.contrib.flask import Sentry
from .blueprints import datastore, package, user, search
from .blueprints.logger import logger


def create():
    """Create application.
    """

    # Create application
    app = Flask('service', static_folder=None)
    app.config['DEBUG'] = True

    # CORS support
    CORS(app)

    # Exception logging
    Sentry(app, dsn=os.environ.get('SENTRY_DSN', ''))

    # Session
    sess = Session()
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = 'openspending rocks'
    sess.init_app(app)

    # Register blueprints
    logger.info("Creating Datastore Blueprint")
    app.register_blueprint(datastore.create(), url_prefix='/datastore/')
    logger.info("Creating Package Blueprint")
    app.register_blueprint(package.create(), url_prefix='/package/')
    logger.info("Creating Authentication Blueprint")
    app.register_blueprint(user.oauth_create(), url_prefix='/oauth/')
    logger.info("Creating Users Blueprint")
    app.register_blueprint(user.create(), url_prefix='/user/')
    logger.info("Creating Search Blueprint")
    app.register_blueprint(search.create(), url_prefix='/search/')

    # Return application
    return app
