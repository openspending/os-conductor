import unittest
from unittest.mock import Mock, patch
from importlib import import_module
module = import_module('authz.blueprints.datastore.controllers')


class AuthorizeTest(unittest.TestCase):

    # Actions

    def setUp(self):
        self.addCleanup(patch.stopall)

    # Tests

    def test(self):
        pass
