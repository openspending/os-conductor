import os
import datetime
import logging
import json
import base64
import zlib

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse  # silence pyflakes

import jwt
import requests
from flask import make_response, redirect
from flask_oauthlib.client import OAuth, OAuthException

from .models import get_permission, get_user, create_or_get_user, save_user


def readfile_or_default(filename, default):
    try:
        return open(filename).read().strip()
    except IOError:
        return default


os_conductor = os.environ.get('OS_EXTERNAL_ADDRESS')

try:
    credentials = ''.join(os.environ.get('OS_CONDUCTOR_SECRETS_%d' % i)
                          for i in range(4)).encode('ascii')
    credentials = base64.decodebytes(credentials)
    credentials = zlib.decompress(credentials).decode('ascii')
    credentials = json.loads(credentials)
except Exception as _:
    credentials = {}

PUBLIC_KEY = credentials.get('public.pem', '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzSrV/SxRNKufc6f0GQIu
YMASgBCOiJW5fvCnGtVMIrWvBQoCFAp9QwRHrbQrQJiPg6YqqnTvGhWssL5LMMvR
8jXXOpFUKzYaSgYaQt1LNMCwtqMB0FGSDjBrbmEmnDSo6g0Naxhi+SJX3BMcce1W
TgKRybv3N3F+gJ9d8wPkyx9xhd3H4200lHk4T5XK5+LyAPSnP7FNUYTdJRRxKFWg
ZFuII+Ex6mtUKU9LZsg9xeAC6033dmSYe5yWfdrFehmQvPBUVH4HLtL1fXTNyXuz
ZwtO1v61Qc1u/j7gMsrHXW+4csjS3lDwiiPIg6q1hTA7QJdB1M+rja2MG+owL0U9
owIDAQAB
-----END PUBLIC KEY-----''')
PRIVATE_KEY = credentials.get('private.pem', '''-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAzSrV/SxRNKufc6f0GQIuYMASgBCOiJW5fvCnGtVMIrWvBQoC
FAp9QwRHrbQrQJiPg6YqqnTvGhWssL5LMMvR8jXXOpFUKzYaSgYaQt1LNMCwtqMB
0FGSDjBrbmEmnDSo6g0Naxhi+SJX3BMcce1WTgKRybv3N3F+gJ9d8wPkyx9xhd3H
4200lHk4T5XK5+LyAPSnP7FNUYTdJRRxKFWgZFuII+Ex6mtUKU9LZsg9xeAC6033
dmSYe5yWfdrFehmQvPBUVH4HLtL1fXTNyXuzZwtO1v61Qc1u/j7gMsrHXW+4csjS
3lDwiiPIg6q1hTA7QJdB1M+rja2MG+owL0U9owIDAQABAoIBAHgA7ytniZQSMnDW
szsRgIkMr4WCqawQT3CFWGikjCTdOiLraK3KONxDG53pfUcKNR9eySPsw5HxTZIP
rDE9dm6CuYJDUQT5X0Ue7qtffsa7UmFxVPVBUPnFroDgiFHjp01HFysmF3X7dYJ/
Fys4FDwK2rUxoXcnhkO7c5taErAPhpmv+QncVBkouQ3bB78av6cHdQfo+7PcvYRP
x6iDPAjMpz1wF1Fkd9mSHadjuqlC3FubbwEK5nTuSl4nPULK7KaCv9NjxyzTUi23
DWk9QCv+peIK/1h75cbB9eVvZayHlFlVNtD7Mrx5rediWABSqvNLRv/aZ0/o5+FM
1cxiYPECgYEA9AEr60CPlW9vBOacCImnWHWEH/UEwi4aNTBxpZEWRuN0HnmB+4Rt
1b+7LoX6olVBN1y8YIwzkDOCVblFaT+THBNiE7ABwB87c0jYd2ULQszqrebjXPoz
8q7MqghD+4iDfvP2QmivpadfeGGzYFI49b7W5c/Iv4w0oWgutib+hDsCgYEA10Dk
hMwg61q6YVAeTIqnV7zujfzTIif9AkePAfNLolLdn0Bx5LS6oPxeRUxyy4mImwrf
p6yZGOX/7ocy7rQ3X/F6fuxwuGa74PNZPwlLuD7UUPr//OPuQihoDKvL+52XWA5U
Q09sXK+KlvuH4DJ5UsHC9kgATyuGNUOeXYBHHbkCgYEA78Zq8x2ZOz6quQUolZc3
dEzezkyHJY4KQPRe6VUesAB5riy3F4M2L5LejMQp2/WtRYsCrll3nh+P109dryRD
GpbNjQ0rWzEVyZ7u4LzRiQ43GzbFfCt+et9czUWcEIRAu7Ne7jlTSZSk03Ymv+Ns
h8jGAkTiP6C2Y1oudN7ywtsCgYBAWIa3Z+oDUQjcJD4adWxW3wSU71oSINASSV/n
nloiuRDFFVe2nYwYqbhokNTUIVXzuwlmr0LI3aBnJoVENB1FkgMjQ/ziMtvBAB3S
qS24cxe26YFykJRdtIR+HTEKE271hLsNsAVdo6ATSDey/oOkCIYGZzmocQNaks8Z
dkpMCQKBgQCfZ75r1l/Hzphb78Ygf9tOz1YUFqw/xY9jfufW4C/5SgV2q2t/AZok
LixyPP8SzJcH20iKdc9kS7weiQA0ldT2SYv6VT7IqgQ3i/qYdOmaggjBGaIuIB/B
QZOJBnaSMVJFf/ZO1/1ilGVGfZZ3TMOA1TJlcTZisk56tRTbkivL9Q==
-----END RSA PRIVATE KEY-----''')
GOOGLE_KEY = credentials.get('google.key', 'google consumer key')
GOOGLE_SECRET = credentials.get('google.secret.key',
                                'google consumer secret')
LIBJS = readfile_or_default(os.path.join(os.path.dirname(__file__),
                                         'lib',
                                         'lib.js'),
                            'alert("error");')

oauth = OAuth()


def _google_remote_app():
    if 'google' not in oauth.remote_apps:
        oauth.remote_app(
            'google',
            base_url='https://www.googleapis.com/oauth2/v1/',
            authorize_url='https://accounts.google.com/o/oauth2/auth',
            request_token_url=None,
            request_token_params={
                'scope': 'email profile',
            },
            access_token_url='https://accounts.google.com/o/oauth2/token',
            access_token_method='POST',
            consumer_key=GOOGLE_KEY,
            consumer_secret=GOOGLE_SECRET)
    return oauth.google


def _get_user_profile(access_token):
    if access_token is None:
        return None
    headers = {'Authorization': 'OAuth {}'.format(access_token)}
    response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo',
                            headers=headers)

    if response.status_code == 401:
        return None

    return response.json()


def authenticate(token, next, callback_url):
    """Check if user is authenticated
    """
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
    google_login_url = _google_remote_app() \
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


def _update_next_url(next_url, client_token):
    if client_token is None:
        return next_url

    url_parts = list(urlparse.urlparse(next_url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update({'jwt': client_token})

    url_parts[4] = urlparse.urlencode(query)

    next_url = urlparse.urlunparse(url_parts)
    return next_url


def _get_token_from_profile(provider, profile):
    if profile is None:
        return None
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
    return client_token


def oauth_callback(state):
    """Callback from google
    """
    try:
        app = _google_remote_app()
        resp = app.authorized_response()
    except OAuthException as e:
        resp = e
    if isinstance(resp, OAuthException):
        logging.error("OAuthException: %r", resp.data, exc_info=resp)
        resp = None

    try:
        state = jwt.decode(state, PRIVATE_KEY)
    except jwt.InvalidTokenError:
        state = {}

    next_url = '/'
    provider = state.get('provider')
    next_url = state.get('next', next_url)
    if resp is not None and provider is not None:
        access_token = resp.get('access_token')
        profile = _get_user_profile(access_token)
        client_token = _get_token_from_profile(provider, profile)
        # Add client token to redirect url
        next_url = _update_next_url(next_url, client_token)

    return redirect(next_url)


def update(token, username):
    """Update a user
    """
    err = None
    if token is not None:
        try:
            token = jwt.decode(token, PRIVATE_KEY)
        except jwt.InvalidTokenError:
            token = None
            err = 'Not authenticated'
    else:
        err = 'No token'

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


def authorize(token, service):
    """Return user authorization for a service
    """
    if token is not None and service is not None:
        try:
            token = jwt.decode(token, PRIVATE_KEY)
        except jwt.InvalidTokenError:
            token = None

        if token is not None:
            userid = token['userid']
            service_permissions = get_permission('*', service)
            user_permissions = get_permission(userid, service)
            permissions = {}
            if service_permissions is not None:
                permissions.update(service_permissions)
            if user_permissions is not None:
                permissions.update(user_permissions)
            ret = {
                'userid': userid,
                'permissions': permissions,
                'service': service
            }
            token = jwt.encode(ret, PRIVATE_KEY, algorithm='RS256')\
                       .decode('ascii')
            ret['token'] = token
            return ret

    ret = {
        'permissions': {}
    }
    return ret


def public_key():
    return PUBLIC_KEY


def lib():
    resp = make_response(LIBJS)
    resp.headers['Content-Type'] = 'text/javascript'
    return resp
