import unittest

import time
import jwt
import datetime
import requests_mock
from collections import namedtuple
from hashlib import md5

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
from importlib import import_module, reload

models = import_module('auth.models')
credentials = import_module('auth.credentials')
models.setup_engine('sqlite://')
models.load_fixtures()

class UserAdminTest(object):

    USERID = 'uusseerriidd'
    NAME = 'nnaammee'
    EMAIL = 'eemmaaiill'
    AVATAR_URL = 'aavvaattaarr__uurrll'
    USERNAME = 'usernaaaame'

    # Actions

    def setUp(self):
        self.ctrl = import_module('auth.controllers')
        self.private_key = credentials.private_key
        reload(self.ctrl)

    def test___create_user___success(self):
        user = models.create_or_get_user(self.USERID, self.NAME, self.USERNAME, self.EMAIL, self.AVATAR_URL)
        self.assertEquals(user['id'], self.USERID)
        self.assertEquals(user['name'], self.NAME)
        self.assertEquals(user['email'], self.EMAIL)
        self.assertEquals(user['avatar_url'], self.AVATAR_URL)

    def test___create__existing_user___success(self):
        models.create_or_get_user(self.USERID, self.NAME, self.USERNAME, self.EMAIL, self.AVATAR_URL)
        user = models.create_or_get_user(self.USERID, self.NAME, self.USERNAME, self.EMAIL, self.AVATAR_URL)
        self.assertEquals(user['id'], self.USERID)
        self.assertEquals(user['name'], self.NAME)
        self.assertEquals(user['email'], self.EMAIL)
        self.assertEquals(user['avatar_url'], self.AVATAR_URL)

    def test___get__existing_user___success(self):
        models.create_or_get_user(self.USERID, self.NAME, self.USERNAME, self.EMAIL, self.AVATAR_URL)
        hash = models.hash_email(self.EMAIL)
        user = models.get_user(hash)
        self.assertEquals(user['id'], self.USERID)
        self.assertEquals(user['name'], self.NAME)
        self.assertEquals(user['email'], self.EMAIL)
        self.assertEquals(user['avatar_url'], self.AVATAR_URL)

    def test___get__nonexisting_user___success(self):
        hash = models.hash_email(self.EMAIL)
        user = models.get_user(hash)
        self.assertIs(user, None)

    def test___save__existing_user___success(self):
        user2 = models.create_or_get_user(self.USERID, self.NAME, self.USERNAME, self.EMAIL, self.AVATAR_URL)
        user2['email'] += 'X'
        models. save_user(user2)
        hash = models.hash_email(self.EMAIL)
        user = models.get_user(hash)
        self.assertEquals(user['id'], self.USERID)
        self.assertEquals(user['name'], self.NAME)
        self.assertEquals(user['email'], self.EMAIL+'X')
        self.assertEquals(user['avatar_url'], self.AVATAR_URL)

    def test___update___no_jwt(self):
        ret = self.ctrl.update(None, 'new_username')
        self.assertFalse(ret.get('success'))
        self.assertEquals(ret.get('error'), 'No token')

    def test___update___bad_jwt(self):
        ret = self.ctrl.update('bla', 'new_username')
        self.assertFalse(ret.get('success'))
        self.assertEquals(ret.get('error'), 'Not authenticated')

    def test___update___no_such_user(self):
        hash = models.hash_email(self.EMAIL+'X')
        token = {
            'userid': hash,
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        client_token = jwt.encode(token, self.private_key)
        ret = self.ctrl.update(client_token, 'new_username')
        self.assertFalse(ret.get('success'))
        self.assertEquals(ret.get('error'), 'Unknown User')

    def test___update___new_user(self):
        models.create_or_get_user(self.USERID, self.NAME, self.USERNAME, self.EMAIL, self.AVATAR_URL)
        hash = models.hash_email(self.EMAIL)
        token = {
            'userid': hash,
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        client_token = jwt.encode(token, self.private_key)
        ret = self.ctrl.update(client_token, 'new_username')
        self.assertTrue(ret.get('success'))
        self.assertEquals(ret.get('error'), None)
        user = models.get_user(hash)
        self.assertEquals(user['username'], 'new_username')


    def test___update___double_update(self):
        models.create_or_get_user(self.USERID, self.NAME, self.USERNAME, self.EMAIL, self.AVATAR_URL)
        hash = models.hash_email(self.EMAIL)
        token = {
            'userid': hash,
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        client_token = jwt.encode(token, self.private_key)
        ret = self.ctrl.update(client_token, 'new_username')
        self.assertTrue(ret.get('success'))
        self.assertEquals(ret.get('error'), None)
        ret = self.ctrl.update(client_token, 'new_username_@')
        self.assertFalse(ret.get('success'))
        self.assertEquals(ret.get('error'), 'Cannot modify username, already set')
        user = models.get_user(hash)
        self.assertEquals(user['username'], 'new_username')


class AuthenticationTest(unittest.TestCase):

    USERID = 'userid'
    IDHASH = md5(USERID.encode('utf8')).hexdigest()

    # Actions

    def setUp(self):

        self.ctrl = import_module('auth.controllers')
        self.private_key = credentials.private_key
        reload(self.ctrl)

        # Cleanup
        self.addCleanup(patch.stopall)

        self.goog_provider = namedtuple("resp",['headers'])({'Location':'google'})
        self.oauth_response = {
            'access_token': 'access_token'
        }
        goog = namedtuple('_google_remote_app',
                          ['authorize', 'authorized_response', 'name'])(
            lambda **kwargs: self.goog_provider,
            lambda **kwargs: self.oauth_response,
            'google'
        )
        self.ctrl.remote_apps['google'] = {
            'app': goog,
            'get_profile': 'https://www.googleapis.com/oauth2/v1/userinfo',
            'auth_header_prefix': 'OAuth '
        }
        self.ctrl.get_user = Mock(
            return_value=namedtuple('User',
                                    ['name','email','avatar_url'])
            ('moshe','email@moshe.com','http://google.com')
        )
        self.ctrl._get_user_profile = Mock(
            return_value={
                'id': 'userid',
                'idhash': self.IDHASH,
                'name': 'Moshe',
                'email': 'email@moshe.com',
                'picture': 'http://moshe.com/picture'
            }
        )

    # Tests

    def test___check___no_jwt(self):
        ret = self.ctrl.authenticate(None, 'next', 'callback', self.private_key)
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___bad_jwt(self):
        ret = self.ctrl.authenticate('bla', 'next', 'callback', self.private_key)
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___good_jwt_no_such_user(self):
        self.ctrl.get_user = Mock(
            return_value=None
        )
        token = {
            'userid': self.IDHASH,
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        client_token = jwt.encode(token, self.private_key)
        ret = self.ctrl.authenticate(client_token, 'next', 'callback', self.private_key)
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___expired_jwt(self):
        token = {
            'userid': self.IDHASH,
            'exp': (datetime.datetime.utcnow() -
                    datetime.timedelta(days=1))
        }
        client_token = jwt.encode(token, self.private_key)
        ret = self.ctrl.authenticate(client_token, 'next', 'callback', self.private_key)
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___good_jwt(self):
        token = {
            'userid': self.IDHASH,
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        client_token = jwt.encode(token, self.private_key)
        ret = self.ctrl.authenticate(client_token, 'next', 'callback', self.private_key)
        self.assertTrue(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('profile'))
        self.assertEquals(ret['profile'].email,'email@moshe.com')
        self.assertEquals(ret['profile'].avatar_url,'http://google.com')
        self.assertEquals(ret['profile'].name,'moshe')

    def test___callback___good_response(self):
        token = {
            'next': 'http://next.com/',
            'provider': 'google',
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        state = jwt.encode(token, self.private_key)
        ret = self.ctrl.oauth_callback(state, 'callback', self.private_key)
        self.assertTrue('jwt' in ret)

    def test___callback___good_response_double(self):
        token = {
            'next': 'http://next.com/',
            'provider': 'google',
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        state = jwt.encode(token, self.private_key)
        ret = self.ctrl.oauth_callback(state, 'callback', self.private_key)
        self.assertTrue('jwt' in ret)
        ret = self.ctrl.oauth_callback(state, 'callback', self.private_key)
        self.assertTrue('jwt' in ret)

    def test___callback___bad_response(self):
        self.oauth_response = None
        token = {
            'next': 'http://next.com/',
            'provider': 'google',
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        state = jwt.encode(token, self.private_key)
        ret = self.ctrl.oauth_callback(state, 'callback', self.private_key)
        self.assertFalse('jwt' in ret)

    def test___callback___bad_state(self):
        ret = self.ctrl.oauth_callback("das", 'callback', self.private_key)
        self.assertFalse('jwt' in ret)


class GetUserProfileTest(unittest.TestCase):

    def setUp(self):

        self.ctrl = import_module('auth.controllers')
        self.private_key = credentials.private_key
        reload(self.ctrl)

        # Cleanup
        self.addCleanup(patch.stopall)

        self.goog_provider = namedtuple("resp",['headers'])({'Location':'google'})
        self.git_provider = namedtuple("resp",['headers'])({'Location':'github'})
        self.oauth_response = {
            'access_token': 'access_token'
        }
        goog = namedtuple('_google_remote_app',
                          ['authorize', 'authorized_response', 'name'])(
            lambda **kwargs: self.goog_provider,
            lambda **kwargs: self.oauth_response,
            'google'
        )
        git = namedtuple('_github_remote_app',
                        ['authorize', 'authorized_response', 'name'])(
            lambda **kwargs: self.git_provider,
            lambda **kwargs: self.oauth_response,
            'github'
        )
        self.ctrl.remote_apps['google'] = {
            'app': goog,
            'get_profile': 'https://www.googleapis.com/oauth2/v1/userinfo',
            'auth_header_prefix': 'OAuth '
        }
        self.ctrl.remote_apps['github'] = {
            'app': git,
            'get_profile': 'https://api.github.com/user',
            'auth_header_prefix': 'OAuth '
        }
        self.mocked_resp = '''
        {
            "name": "Moshe",
            "email": "email@moshe.com"
        }
        '''

    # Tests

    def test___check___getting_none_if_no_token(self):
        res = self.ctrl._get_user_profile('google', None)
        self.assertIsNone(res)

    def test___check___google_works_fine(self):
        with requests_mock.Mocker() as mock:
            mock.get('https://www.googleapis.com/oauth2/v1/userinfo',
                    text=self.mocked_resp)
            res = self.ctrl._get_user_profile('google', 'access_token')
            self.assertEquals(res['email'], 'email@moshe.com')
            self.assertEquals(res['name'], 'Moshe')


    def test___check___git_works_fine_with_public_email(self):
        with requests_mock.Mocker() as mock:
            mock.get('https://api.github.com/user', text=self.mocked_resp)
            res = self.ctrl._get_user_profile('github', 'access_token')
            self.assertEquals(res['email'], 'email@moshe.com')
            self.assertEquals(res['name'], 'Moshe')

    def test___check___git_works_fine_with_private_email(self):
        self.mocked_resp = '''
        {
            "name": "Moshe",
            "email": null
        }
        '''
        emails_resp = '''
        [{
            "email": "email@moshe.com",
            "primary": true,
            "verified": true
         }]
        '''
        with requests_mock.Mocker() as mock:
            mock.get('https://api.github.com/user', text=self.mocked_resp)
            mock.get('https://api.github.com/user/emails', text=emails_resp)
            res = self.ctrl._get_user_profile('github', 'access_token')
            self.assertEquals(res['email'], 'email@moshe.com')
            self.assertEquals(res['name'], 'Moshe')


class NormalizeProfileTestCase(unittest.TestCase):

    def setUp(self):

        self.ctrl = import_module('auth.controllers')

        # Cleanup
        self.addCleanup(patch.stopall)


    def test__normilize_profile_from_github(self):
        git_response = {
            'id': 'gituserid',
            'login': 'NotMoshe',
            'name': 'Not Moshe',
            'email': 'git_email@moshe.com'
        }
        out = self.ctrl._normilize_profile('github', git_response)
        self.assertEquals(out['username'], 'NotMoshe')

    def test__normilize_profile_from_google(self):
        google_response = {
            'id': 'userid',
            'name': 'Moshe',
            'email': 'google_email@moshe.com'
        }
        out = self.ctrl._normilize_profile('google', google_response)
        self.assertEquals(out['username'], 'google_email')

    def test__adds_number_if_username_already_exists(self):
        models.save_user({
            'id': 'new_userid',
            'provider_id': '',
            'username': 'existing_username',
            'name': 'Moshe',
            'email': 'email@moshe.com',
            'avatar_url': 'http://avatar.com',
            'join_date': datetime.datetime.now()
        })
        google_response = {
            'id': 'userid',
            'username': 'existing_username',
            'name': 'Moshe',
            'email': 'existing_username@moshe.com'
        }
        out = self.ctrl._normilize_profile('google', google_response)
        self.assertEquals(out['username'], 'existing_username1')


class ResolveUsernameTest(unittest.TestCase):

    def setUp(self):

        self.ctrl = import_module('auth.controllers')

        self.private_key = credentials.private_key
        reload(self.ctrl)

        # Cleanup
        self.addCleanup(patch.stopall)

    def test___resolve_username___existing_user(self):
        self.ctrl.get_user_by_username = Mock(
            return_value={'id': 'abc123'}
        )
        username = 'existing_user'
        ret = self.ctrl.resolve_username(username)
        self.assertEquals(ret['userid'], 'abc123')

    def test___resolve_username___nonexisting_user(self):
        username = 'nonexisting_user'
        ret = self.ctrl.resolve_username(username)
        self.assertEquals(ret['userid'], None)


class GetUserProfileByUsernameTest(unittest.TestCase):

    def setUp(self):

        self.ctrl = import_module('auth.controllers')

        self.private_key = credentials.private_key
        reload(self.ctrl)

        # Cleanup
        self.addCleanup(patch.stopall)

    def test___get_profile_by_username___existing_user(self):
        return_value = {
            'id': 'abc123',
            'email': 'test@test.com',
            'join_date': 'Mon, 24 Jul 2017 12:17:50 GMT',
            'name': 'Test Test'
        }
        self.ctrl.get_user_by_username = Mock(
            return_value=return_value
        )
        username = 'existing_user'
        ret = self.ctrl.get_profile_by_username(username)
        self.assertEquals(ret['profile']['id'], return_value['id'])
        self.assertEquals(ret['profile']['join_date'], return_value['join_date'])
        self.assertEquals(ret['found'], True)

    def test___get_profile_by_username___nonexisting_user(self):
        username = 'nonexisting_user'
        ret = self.ctrl.get_profile_by_username(username)
        self.assertEquals(ret['profile'], None)
        self.assertEquals(ret['found'], False)
