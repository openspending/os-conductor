import unittest

import jwt
from collections import namedtuple

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
from importlib import import_module

module = import_module('auth.controllers')
credentials = import_module('auth.credentials')


def client_token():
    token = {
        'userid': 'userid',
    }
    return jwt.encode(token, credentials.private_key)


class AuthorizationTest(unittest.TestCase):

    # Actions

    def setUp(self):

        # Cleanup
        self.addCleanup(patch.stopall)

        goog_provider = namedtuple("resp",['headers'])({'Location':'google'})
        oauth_response = {
            'access_token': 'access_token'
        }
        module.google_remote_app = Mock(
            return_value=namedtuple('google_remote_app',
                                    ['authorize', 'authorized_response'])
            (authorize=lambda **kwargs:goog_provider,
             authorized_response=lambda **kwargs:oauth_response)
        )
        self.private_key = credentials.private_key

    # Tests

    def test___check___no_token(self):
        ret = module.authorize(None, 'service', self.private_key)
        self.assertEquals(ret.get('permissions'), {})

    def test___check___no_service(self):
        ret = module.authorize('token', None, self.private_key)
        self.assertEquals(ret.get('permissions'), {})

    def test___check___bad_token_not_allowed_service(self):
        ret = module.authorize('token', 'servis', self.private_key)
        self.assertEquals(ret.get('permissions'), {})

    def test___check___bad_token(self):
        ret = module.authorize('token', 'example', self.private_key)
        self.assertEquals(ret.get('permissions'), {})

    def test___check___good_token_not_allowed_service(self):
        ret = module.authorize(client_token(), 'servis', self.private_key)
        self.assertEquals(ret.get('permissions'), {})

    def test___check___good_token_good_service(self):
        ret = module.authorize(client_token(), 'example', self.private_key)
        self.assertEquals(ret.get('service'), 'example')
        self.assertEquals(ret.get('permissions'),{
            'provider-token': 'example-userid'
        })

    def test___check___good_token_good_service2(self):
        ret = module.authorize(client_token(), 'example2', self.private_key)
        self.assertEquals(ret.get('service'), 'example2')
        self.assertEquals(ret.get('permissions'),{
            'provider-token': 'example2-userid'
        })
