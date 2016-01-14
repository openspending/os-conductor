import boto
import json
import unittest
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
import conductor


class datastoreTest(unittest.TestCase):

    # Actions

    def setUp(self):

        # Patches
        self.addCleanup(patch.stopall)
        self.connect_s3 = patch.object(boto, 'connect_s3').start()
        self.connect_s3().get_bucket().new_key().generate_url = Mock(
                return_value='http://test.com?key=value')

        # App and payload
        self.app = conductor.create().test_client()
        self.payload = {
            'metadata': {
                'owner': 'owner',
                'name': 'name',
            },
            'filedata': {
                'file1': {
                    'name': 'file1',
                    'length': 100,
                    'md5': 'aaa',
                },
            },
        }

    # Tests

    def test_not_authorized(self):
        res = self.app.post(
                '/datastore/',
                data=json.dumps(self.payload))
        self.assertEqual(res.status, '401 UNAUTHORIZED')

    def test_bad_request(self):
        patch('conductor.config.API_KEY_WHITELIST', 'key1,key2').start()
        res = self.app.post(
                '/datastore/',
                headers={'API-Key': 'key1'},
                data=json.dumps({'bad': 'data'}))
        self.assertEqual(res.status, '400 BAD REQUEST')

    def test_good_request(self):
        patch('conductor.config.API_KEY_WHITELIST', 'key1,key2').start()
        res = self.app.post(
                '/datastore/',
                headers={'API-Key': 'key1'},
                data=json.dumps(self.payload))
        self.assertEqual(json.loads(res.data.decode('utf-8')), {
            'filedata': {
                'file1': {
                    'name': 'file1',
                    'length': 100,
                    'md5': 'aaa',
                    'upload_url': 'http://test.com',
                    'upload_query': {'key': ['value']},
                },
            },
        })
