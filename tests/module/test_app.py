import unittest
from unittest.mock import Mock, patch
from importlib import import_module
module = import_module('authz.app')


class createTest(unittest.TestCase):

    # Actions

    def setUp(self):
        self.addCleanup(patch.stopall)
        self.datastore = patch.object(module, 'datastore').start()

    # Tests

    def test(self):
        self.assertTrue(module.create())
