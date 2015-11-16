import unittest
from unittest.mock import Mock, patch
from importlib import import_module
module = import_module('authz.blueprints.datastore.services')


class VerifyTest(unittest.TestCase):

    # Actions

    def setUp(self):
        self.addCleanup(patch.stopall)
        self.config = patch.object(module, 'config').start()
        self.config.API_KEY_WHITELIST = 'key1,key2'

    # Tests

    def test_verified(self):
        self.assertTrue(module.verify('key1'))
        self.assertTrue(module.verify('key2'))

    def test_not_verified(self):
        self.assertFalse(module.verify('key3'))
