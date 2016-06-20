import requests
import datetime
import logging

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
import jwt

from flask import redirect
from flask_oauthlib.client import OAuth, OAuthException

from .models import create_or_get_user, get_user, save_user


def readfile_or_default(filename, default):
    try:
        return open(filename).read().strip()
    except IOError:
        return default

PRIVATE_KEY = readfile_or_default('/secrets/private.pem', 'private key stub')
GOOGLE_KEY = readfile_or_default('/secrets/google.key', 'google consumer key')
GOOGLE_SECRET = readfile_or_default('/secrets/google.secret.key',
                                    'google consumer secret')

oauth = OAuth()


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
            consumer_key=GOOGLE_KEY,
            consumer_secret=GOOGLE_SECRET)
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

    def __call__(self, token, next, callback_url):
        if token is not None:
            try:
                token = jwt.decode(token, PRIVATE_KEY)
            except jwt.InvalidTokenError:
                token = None

            if token is not None:
                userid = token['userid']
                user = get_user(userid)
                if user is not None:
                    ret = {
                        'authenticated': True,
                        'profile': user
                    }
                    return ret

        # Otherwise - not authenticated
        provider = 'google'
        state = {
            'next': next,
            'provider': provider,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
            'nbf': datetime.datetime.utcnow()
        }
        state = jwt.encode(state, PRIVATE_KEY)
        google_login_url = google_remote_app()\
            .authorize(callback=callback_url, state=state).headers['Location']

        ret = {
            'authenticated': False,
            'providers': {
                'google': {
                    'url': google_login_url
                }
            }
        }

        return ret


class Callback:
    """Callback from google
    """

    # Public

    def __call__(self, state):
        resp = google_remote_app().authorized_response()
        if isinstance(resp, OAuthException):
            logging.log(logging.WARN, "OAuthException: %r" % resp)
            resp = None

        try:
            state = jwt.decode(state, PRIVATE_KEY)
        except jwt.InvalidTokenError:
            state = None

        next_url = '/'
        provider = None
        if state is not None:
            provider = state.get('provider')
            next_url = state.get('next', next_url)
        if resp is not None and provider is not None:
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
                    'userid': user['idhash'],
                    'exp': (datetime.datetime.utcnow() +
                            datetime.timedelta(days=14))
                }
                client_token = jwt.encode(token, PRIVATE_KEY)
            if client_token is not None:
                # Add client token to redirect url
                url_parts = list(urlparse.urlparse(next_url))
                query = dict(urlparse.parse_qsl(url_parts[4]))
                query.update({'jwt': client_token})

                url_parts[4] = urlparse.urlencode(query)

                next_url = urlparse.urlunparse(url_parts)

        return redirect(next_url)


class Update:
    """Update a user
    """

    # Public

    def __call__(self, token, username):
        err = None
        if token is not None:
            try:
                token = jwt.decode(token, PRIVATE_KEY)
            except jwt.InvalidTokenError:
                token = None
                err = 'Not authenticated'
        else:
            err = 'No token'

        user = None
        if token is not None:
            userid = token['userid']
            user = get_user(userid)

            if user is not None:
                dirty = False
                if username is not None:
                    if user.get('username') is None:
                        user['username'] = username
                        dirty = True
                    else:
                        err = 'Cannot modify username, already set'
                if dirty:
                    save_user(user)
            else:
                err = 'Unknown User'

        ret = {'success': err is None}
        if err is not None:
            ret['error'] = err

        return ret
