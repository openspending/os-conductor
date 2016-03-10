import unittest

import flask
import jwt
import datetime
from collections import namedtuple

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
from importlib import import_module
module = import_module('conductor.blueprints.authentication.controllers')


class AuthenticationTest(unittest.TestCase):

    # Actions

    def setUp(self):

        # Cleanup
        self.addCleanup(patch.stopall)

        self.goog_provider = namedtuple("resp",['headers'])({'Location':'google'})
        self.oauth_response = {
            'access_token': 'access_token'
        }
        module.google_remote_app = Mock(
            return_value=namedtuple('google_remote_app',
                                    ['authorize', 'authorized_response'])
            (authorize=lambda **kwargs: self.goog_provider,
             authorized_response=lambda **kwargs: self.oauth_response)
        )
        module.get_user = Mock(
            return_value=namedtuple('User',
                                    ['name','email','avatar_url'])
            ('moshe','email@moshe.com','http://google.com')
        )
        module.get_user_profile = Mock(
            return_value={
                'id': 'userid',
                'name': 'Moshe',
                'email': 'email@moshe.com',
                'picture': 'http://moshe.com/picture'
            }
        )

    # Tests

    def test___check___no_jwt(self):
        ret = module.Check()(None, 'next', 'callback')
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___bad_jwt(self):
        ret = module.Check()('bla', 'next', 'callback')
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___good_jwt_no_such_user(self):
        module.get_user = Mock(
            return_value=None
        )
        token = {
            'userid': 'userid',
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        client_token = jwt.encode(token, 'private key stub')
        ret = module.Check()(client_token, 'next', 'callback')
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___expired_jwt(self):
        token = {
            'userid': 'userid',
            'exp': (datetime.datetime.utcnow() -
                    datetime.timedelta(days=1))
        }
        client_token = jwt.encode(token, 'private key stub')
        ret = module.Check()(client_token, 'next', 'callback')
        self.assertFalse(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('providers',{}).get('google'))

    def test___check___good_jwt(self):
        token = {
            'userid': 'userid',
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        client_token = jwt.encode(token, 'private key stub')
        ret = module.Check()(client_token, 'next', 'callback')
        self.assertTrue(ret.get('authenticated'))
        self.assertIsNotNone(ret.get('profile'))
        self.assertEquals(ret['profile']['email'],'email@moshe.com')
        self.assertEquals(ret['profile']['avatar_url'],'http://google.com')
        self.assertEquals(ret['profile']['name'],'moshe')

    def test___callback___good_response(self):
        token = {
            'next': 'http://next.com/',
            'provider': 'dummy',
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        state = jwt.encode(token, 'private key stub')
        ret = module.Callback()(state)
        self.assertEqual(ret.status_code, 302)
        print(ret.headers['Location'])
        self.assertTrue('jwt' in ret.headers['Location'])

    def test___callback___bad_response(self):
        self.oauth_response = None
        token = {
            'next': 'http://next.com/',
            'provider': 'dummy',
            'exp': (datetime.datetime.utcnow() +
                    datetime.timedelta(days=14))
        }
        state = jwt.encode(token, 'private key stub')
        ret = module.Callback()(state)
        self.assertEqual(ret.status_code, 302)
        self.assertFalse('jwt' in ret.headers['Location'])

    def test___callback___bad_state(self):
        ret = module.Callback()("das")
        self.assertEqual(ret.status_code, 302)
        self.assertFalse('jwt' in ret.headers['Location'])

