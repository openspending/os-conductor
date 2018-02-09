import os
import logging

from flask import Flask
from flask_cors import CORS
from flask_session import Session

from auth import make_blueprint

# Create application
app = Flask(__name__, static_folder=None)

# CORS support
CORS(app, supports_credentials=True)

# Session
sess = Session()
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp/sessions'
app.config['SECRET_KEY'] = '-'
sess.init_app(app)

# Register blueprints
app.register_blueprint(make_blueprint(os.environ.get('EXTERNAL_ADDRESS')),
                        url_prefix='/auth/')


logging.getLogger().setLevel(logging.INFO)

if __name__=='__main__':
    app.run(port=3000)
