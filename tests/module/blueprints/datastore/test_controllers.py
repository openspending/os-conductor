import json
import unittest
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
from importlib import import_module
module = import_module('conductor.blueprints.datastore.controllers')


class AuthorizeTest(unittest.TestCase):

    # Actions

    def setUp(self):

        # Cleanup
        self.addCleanup(patch.stopall)

        # Request patch
        self.request = patch.object(module, 'request').start()
        self.request.data.decode = Mock(return_value=json.dumps({
            'metadata': {
                'owner': 'owner',
                'name': 'name',
            },
            'filedata': {
                'data/file1': {
                    'name': 'file1',
                    'length': 100,
                    'md5': 'aaa',
                },
            },
        }))

        # Various patches
        self.services = patch.object(module, 'services').start()
        self.config = patch.object(module, 'config').start()
        self.boto = patch.object(module, 'boto').start()
        self.bucket = self.boto.connect_s3().get_bucket()
        self.bucket.new_key().generate_url = Mock(
                return_value='http://test.com?key=value')

    # Tests

    def test___call___not_authorized(self):
        authorize = module.Authorize()
        self.services.verify = Mock(return_value=False)
        self.assertEqual(authorize().status, '401 UNAUTHORIZED')

    def test___call___bad_request(self):
        authorize = module.Authorize()
        self.request.data.decode = Mock(return_value=json.dumps({
            'bad': 'data',
        }))
        self.assertEqual(authorize().status, '400 BAD REQUEST')

    def test___call___good_request(self):
        authorize = module.Authorize()
        self.assertEqual(json.loads(authorize()), {
            'filedata': {
                'data/file1': {
                    'name': 'file1',
                    'length': 100,
                    'md5': 'aaa',
                    'upload_url': 'http://test.com',
                    'upload_query': {'key': ['value']},
                },
            },
        })
        self.bucket.new_key.assert_called_with('owner/name/data/file1')
