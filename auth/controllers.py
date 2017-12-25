import datetime
import logging

import urllib.parse as urlparse

import jwt
import requests

from flask_oauthlib.client import OAuth, OAuthException

from .permissions import get_token
from .models import get_user, create_or_get_user, save_user, get_user_by_username


oauth = OAuth()
remote_apps = {}


def setup_oauth_apps(*,
                     google_key=None,
                     google_secret=None,
                     github_key=None,
                     github_secret=None):
    # Google
    if all([google_key, google_secret]):
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
            consumer_key=google_key,
            consumer_secret=google_secret)
        remote_apps['google'] = {
            'app': oauth.google,
            'get_profile': 'https://www.googleapis.com/oauth2/v1/userinfo',
            'auth_header_prefix': 'OAuth '
        }

    # GitHub
    if all([github_key, github_secret]):
        oauth.remote_app(
            'github',
            base_url='https://api.github.com/',
            authorize_url='https://github.com/login/oauth/authorize',
            request_token_url=None,
            request_token_params={
                'scope': 'user:email',
            },
            access_token_url='https://github.com/login/oauth/access_token',
            access_token_method='POST',
            consumer_key=github_key,
            consumer_secret=github_secret)
        remote_apps['github'] = {
            'app': oauth.github,
            'get_profile': 'https://api.github.com/user',
            'auth_header_prefix': 'token '
        }


def _get_user_profile(provider, access_token):
    if access_token is None:
        return None
    remote_app = remote_apps[provider]
    headers = {'Authorization': '{}{}'.format(remote_app['auth_header_prefix'], access_token)}
    response = requests.get(remote_app['get_profile'],
                            headers=headers)

    if response.status_code == 401:
        return None

    response = response.json()
    # Make sure we have private Emails from github
    if provider == 'github' and response['email'] is None:
        emails_resp = requests.get(remote_app['get_profile'] + '/emails', headers=headers)
        for email in emails_resp.json():
            if email.get('primary'):
                response['email'] = email['email']
                break

    return response


def authenticate(token, next, callback_url, private_key):
    """Check if user is authenticated
    """
    if token is not None:
        try:
            token = jwt.decode(token, private_key)
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
    providers = {}
    for provider, params in remote_apps.items():
        state = {
            'next': next,
            'provider': provider,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
            'nbf': datetime.datetime.utcnow()
        }
        state = jwt.encode(state, private_key)
        login_url = params['app'] \
            .authorize(callback=callback_url, state=state).headers['Location']
        providers[provider] = {'url': login_url}
    ret = {
        'authenticated': False,
        'providers': providers
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


def _get_token_from_profile(provider, profile, private_key):
    norm_profile = _normilize_profile(provider, profile)
    if norm_profile is None:
        return None
    userid = norm_profile['userid']
    name = norm_profile['name']
    username = norm_profile['username']
    email = norm_profile['email']
    avatar_url = norm_profile['avatar_url']
    user = create_or_get_user(userid, name, username, email, avatar_url)
    logging.info('Got USER %r', user)
    token = {
        'userid': user['id'],
        'exp': (datetime.datetime.utcnow() +
                datetime.timedelta(days=14))
    }
    client_token = jwt.encode(token, private_key)
    return client_token


def _normilize_profile(provider, profile):
    if profile is None:
        return None
    provider_id = profile['id']
    name = profile['name']
    email = profile.get('email')
    if email is None:
        return None
    username = email.split('@')[0]
    if provider == 'github':
        username = profile.get('login')
    fixed_username = username
    suffix = 1
    while get_user_by_username(username) is not None:
        username = '{}{}'.format(fixed_username, suffix)
        suffix += 1
    avatar_url = profile.get('picture', profile.get('avatar_url'))
    userid = '%s:%s' % (provider, provider_id)
    normilized_profile = dict(
        provider_id=provider_id,
        name=name,
        email=email,
        username=username,
        avatar_url=avatar_url,
        userid=userid
    )
    return normilized_profile


def oauth_callback(state, callback_url, private_key,
                   set_session=lambda k, v: None):
    """Callback from google
    """
    try:
        state = jwt.decode(state, private_key)
    except jwt.InvalidTokenError:
        state = {}

    resp = None

    provider = state.get('provider')
    if provider is not None:
        try:
            app = remote_apps[provider]['app']
            set_session('%s_oauthredir' % app.name, callback_url)
            resp = app.authorized_response()
        except OAuthException as e:
            resp = e
        if isinstance(resp, OAuthException):
            logging.error("OAuthException: %r", resp.data, exc_info=resp)
            resp = None

    next_url = '/'
    provider = state.get('provider')
    next_url = state.get('next', next_url)
    if resp is not None and provider is not None:
        access_token = resp.get('access_token')
        logging.info('Got ACCES TOKEN %r', access_token)
        profile = _get_user_profile(provider, access_token)
        logging.info('Got PROFILE %r', profile)
        client_token = _get_token_from_profile(provider, profile, private_key)
        # Add client token to redirect url
        next_url = _update_next_url(next_url, client_token)

    return next_url


def update(token, username, private_key):
    """Update a user
    """
    err = None
    if token is not None:
        try:
            token = jwt.decode(token, private_key)
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


def authorize(token, service, private_key):
    """Return user authorization for a service
    """
    if token is not None and service is not None:
        try:
            token = jwt.decode(token, private_key)
        except jwt.InvalidTokenError:
            token = None

        if token is not None:
            userid = token['userid']
            permissions = get_token(service, userid)
            ret = {
                'userid': userid,
                'permissions': permissions,
                'service': service
            }
            token = jwt.encode(ret, private_key, algorithm='RS256')\
                       .decode('ascii')
            ret['token'] = token
            return ret

    ret = {
        'permissions': {}
    }
    return ret


def resolve_username(username):
    """Return userid for given username. If not exist, return None.
    """
    ret = {'userid': None}
    user = get_user_by_username(username)
    if user is not None:
        ret['userid'] = user['id']
    return ret


def get_profile_by_username(username):
    """Return user profile for given username. If not exist, return None.
    """
    ret = {'found': False, 'profile': None}
    user = get_user_by_username(username)
    if user is not None:
        ret['found'] = True
        ret['profile'] = {
            'id': user['id'],
            'name': user['name'],
            'join_date': user['join_date']
        }
    return ret
