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
        self.assertEquals(len(ret.get('permissions')), 0)

    def test___check___no_service(self):
        ret = module.authorize('token', 'service', self.private_key)
        self.assertEquals(len(ret.get('permissions')), 0)

    def test___check___bad_token(self):
        ret = module.authorize('token', 'service', self.private_key)
        self.assertEquals(len(ret.get('permissions')), 0)

    def test___check___good_token(self):
        token = {
            'userid': 'userid',
        }
        client_token = jwt.encode(token, self.private_key)
        ret = module.authorize(client_token, 'world', self.private_key)
        self.assertEquals(ret.get('service'), 'world')
        self.assertGreater(len(ret.get('permissions',{})), 0)
