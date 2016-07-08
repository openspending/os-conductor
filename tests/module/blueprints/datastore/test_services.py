import unittest

import jwt

from conductor.blueprints.user.controllers import PRIVATE_KEY

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
from importlib import import_module
module = import_module('conductor.blueprints.datastore.services')
token = {
    'userid': 'bla',
    'permissions': {'datapackage-upload': True},
    'service': 'os.datastore'
}
token = jwt.encode(token, PRIVATE_KEY, algorithm='RS256') \
    .decode('ascii')


class VerifyTest(unittest.TestCase):

    # Actions

    def setUp(self):
        self.addCleanup(patch.stopall)

    # Tests

    def test_verified(self):
        self.assertTrue(module.verify(token, 'bla'))
        self.assertTrue(module.verify('testing-token', '__tests'))

    def test_not_verified(self):
        self.assertFalse(module.verify('key3', 'bla'))
        self.assertFalse(module.verify('testing-token', 'bla'))
        self.assertFalse(module.verify('bla', '__tests'))
