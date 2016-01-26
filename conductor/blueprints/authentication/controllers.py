from __future__ import print_function
import os
import requests
import datetime

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
import jwt

from flask import request, url_for, redirect, send_from_directory
from flask.ext.jsonpify import jsonpify
from flask_oauthlib.client import OAuth, OAuthException

from .models import create_or_get_user, get_user

oauth = OAuth()

SECRET = 'super secret password'
GOOGLE_DEV_KEY = '791676150192-441k9uar5nca2245hv82161saorrc090.' \
                 'apps.googleusercontent.com'
GOOGLE_DEV_SECRET = '5uOZ1v-Rifg7zZVXPQ3ZwLk4'


def google_remote_app():
    if 'google' not in oauth.remote_apps:
        oauth.remote_app(
            'google',
            base_url='https://www.google.com/accounts/',
            authorize_url='https://accounts.google.com/o/oauth2/auth',
            request_token_url=None,
            request_token_params={
                  'scope': 'https://www.googleapis.com/auth/userinfo.email ' +
                           'https://www.googleapis.com/auth/userinfo.profile',
            },
            access_token_url='https://accounts.google.com/o/oauth2/token',
            access_token_method='POST',
            consumer_key=GOOGLE_DEV_KEY,
            consumer_secret=GOOGLE_DEV_SECRET)
    return oauth.google


def get_user_profile(access_token):
    headers = {'Authorization': 'OAuth {}'.format(access_token)}
    response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo',
                            headers=headers)

    if response.status_code == 401:
        return None

    return response.json()


class Check:
    """Check if user is authenticated
    """

    # Public

    def __call__(self):
        token = request.values.get('jwt')
        if token is not None:
            try:
                token = jwt.decode(token, SECRET)
            except jwt.InvalidTokenError:
                token = None

            if token is not None:
                userid = token['userid']
                user = get_user(userid)
                if user is not None:
                    ret = {
                        'authenticated': True,
                        'profile': {
                            'name': user.name,
                            'email': user.email,
                            'avatar_url': user.avatar_url
                        }
                    }
                    return jsonpify(ret)

        # Otherwise - not authenticated
        callback = 'http://conductor.dev.openspending.org'+url_for('.callback')
        next = request.args.get('next', None)
        provider = 'google'
        state = {
            'next': next,
            'provider': provider,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
            'nbf': datetime.datetime.utcnow()
        }
        state = jwt.encode(state, SECRET)
        google_login_url = google_remote_app()\
            .authorize(callback=callback, state=state).headers['Location']

        ret = {
            'authenticated': False,
            'providers': {
                'google': {
                    'url': google_login_url
                }
            }
        }
        return jsonpify(ret)


class Callback:
    """Callback from google
    """

    # Public

    def __call__(self):
        resp = google_remote_app().authorized_response()
        if isinstance(resp, OAuthException):
            resp = None

        state = request.args.get('state')
        try:
            state = jwt.decode(state, SECRET)
        except jwt.InvalidTokenError:
            state = None

        next_url = '/'
        if state is not None and resp is not None:
            provider = state['provider']
            next_url = state['next']
            access_token = resp['access_token']
            profile = None
            client_token = None
            if access_token is not None:
                profile = get_user_profile(access_token)
            if profile is not None:
                provider_id = profile['id']
                name = profile['name']
                email = profile['email']
                avatar_url = profile['picture']
                userid = '%s:%s' % (provider, provider_id)
                user = create_or_get_user(userid, name, email, avatar_url)
                token = {
                    'userid': user.id,
                    'exp': (datetime.datetime.utcnow() +
                            datetime.timedelta(minutes=5))
                }
                client_token = jwt.encode(token, SECRET)
            if client_token is not None:
                # Add client token to redirect url
                url_parts = list(urlparse.urlparse(next_url))
                query = dict(urlparse.parse_qsl(url_parts[4]))
                query.update({'jwt': client_token})

                url_parts[4] = urlparse.urlencode(query)

                next_url = urlparse.urlunparse(url_parts)

        return redirect(next_url)


class Sample:

    def __call__(self, path):
        return send_from_directory(
                        os.path.join(os.path.dirname(__file__), 'lib'),
                        path)
