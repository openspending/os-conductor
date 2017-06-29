import unittest

import time
import jwt
import datetime
from collections import namedtuple
from hashlib import md5

from elasticsearch import Elasticsearch, NotFoundError

from tests.module.blueprints.config import LOCAL_ELASTICSEARCH

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
from importlib import import_module, reload

models = import_module('conductor.blueprints.user.models')

class UserAdminTest(unittest.TestCase):

    USERID = 'uusseerriidd'
    NAME = 'nnaammee'
    EMAIL = 'eemmaaiill'
    AVATAR_URL = 'aavvaattaarr__uurrll'

    # Actions

    def setUp(self):

        self.ctrl = import_module('conductor.blueprints.user.controllers')
        self.private_key = self.ctrl.PRIVATE_KEY
        reload(self.ctrl)

        # Clean index
        self.es = Elasticsearch(hosts=[LOCAL_ELASTICSEARCH])
        try:
            self.es.indices.delete(index='users')
        except NotFoundError:
            pass
        self.es.indices.create('users')
        time.sleep(1)

    def test___create_user___success(self):
        user = models.create_or_get_user(self.USERID, self.NAME, self.EMAIL, self.AVATAR_URL)
        self.assertEquals(user['id'], self.USERID)
        self.assertEquals(user['name'], self.NAME)
        self.assertEquals(user['email'], self.EMAIL)
        self.assertEquals(user['avatar_url'], self.AVATAR_URL)

    def test___create__existing_user___success(self):
        models.create_or_get_user(self.USERID, self.NAME, self.EMAIL, self.AVATAR_URL)
        user = models.create_or_get_user(self.USERID, self.NAME, self.EMAIL, self.AVATAR_URL)
        self.assertEquals(user['id'], self.USERID)
        self.assertEquals(user['name'], self.NAME)
        self.assertEquals(user['email'], self.EMAIL)
        self.assertEquals(user['avatar_url'], self.AVATAR_URL)

    def test___get__existing_user___success(self):
        models.create_or_get_user(self.USERID, self.NAME, self.EMAIL, self.AVATAR_URL)
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
        user2 = models.create_or_get_user(self.USERID, self.NAME, self.EMAIL, self.AVATAR_URL)
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
        models.create_or_get_user(self.USERID, self.NAME, self.EMAIL, self.AVATAR_URL)
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
        models.create_or_get_user(self.USERID, self.NAME, self.EMAIL, self.AVATAR_URL)
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

        self.ctrl = import_module('conductor.blueprints.user.controllers')
        self.private_key = self.ctrl.PRIVATE_KEY
        reload(self.ctrl)

        # Cleanup
        self.addCleanup(patch.stopall)

        self.goog_provider = namedtuple("resp",['headers'])({'Location':'google'})
        self.oauth_response = {
            'access_token': 'access_token'
        }
        self.ctrl._google_remote_app = Mock(
            return_value=namedtuple('_google_remote_app',
                                    ['name', 'authorize', 'authorized_response'])
            (name='_google_remote_app',
             authorize=lambda **kwargs: self.goog_provider,
             authorized_response=lambda **kwargs: self.oauth_response)
        )
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
        ret = self.ctrl.authenticate(None, 'next', 'callback')
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___bad_jwt(self):
        ret = self.ctrl.authenticate('bla', 'next', 'callback')
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
        ret = self.ctrl.authenticate(client_token, 'next', 'callback')
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___expired_jwt(self):
        token = {
            'userid': self.IDHASH,
            'exp': (datetime.datetime.utcnow() -
                    datetime.timedelta(days=1))
        }
        client_token = jwt.encode(token, self.private_key)
        ret = self.ctrl.authenticate(client_token, 'next', 'callback')
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___good_jwt(self):
        token = {
            'userid': self.IDHASH,
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        client_token = jwt.encode(token, self.private_key)
        ret = self.ctrl.authenticate(client_token, 'next', 'callback')
        self.assertTrue(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('profile'))
        self.assertEquals(ret['profile'].email,'email@moshe.com')
        self.assertEquals(ret['profile'].avatar_url,'http://google.com')
        self.assertEquals(ret['profile'].name,'moshe')

    def test___callback___good_response(self):
        token = {
            'next': 'http://next.com/',
            'provider': 'dummy',
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        state = jwt.encode(token, self.private_key)
        callback_url = 'http://example.com/callback'
        ret = self.ctrl.oauth_callback(state, callback_url)
        self.assertEqual(ret.status_code, 302)
        self.assertTrue('jwt' in ret.headers['Location'])

    def test___callback___good_response_double(self):
        token = {
            'next': 'http://next.com/',
            'provider': 'dummy',
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        state = jwt.encode(token, self.private_key)
        callback_url = 'http://example.com/callback'
        ret = self.ctrl.oauth_callback(state, callback_url)
        self.assertEqual(ret.status_code, 302)
        self.assertTrue('jwt' in ret.headers['Location'])
        ret = self.ctrl.oauth_callback(state, callback_url)
        self.assertEqual(ret.status_code, 302)
        self.assertTrue('jwt' in ret.headers['Location'])

    def test___callback___bad_response(self):
        self.oauth_response = None
        token = {
            'next': 'http://next.com/',
            'provider': 'dummy',
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        state = jwt.encode(token, self.private_key)
        callback_url = 'http://example.com/callback'
        ret = self.ctrl.oauth_callback(state, callback_url)
        self.assertEqual(ret.status_code, 302)
        self.assertFalse('jwt' in ret.headers['Location'])

    def test___callback___bad_state(self):
        callback_url = 'http://example.com/callback'
        ret = self.ctrl.oauth_callback("das", callback_url)
        self.assertEqual(ret.status_code, 302)
        self.assertFalse('jwt' in ret.headers['Location'])

