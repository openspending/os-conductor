import json
import requests
from collections import namedtuple
import unittest

from werkzeug.exceptions import BadRequest, NotFound

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
from importlib import import_module
module = import_module('conductor.blueprints.apiload.controllers')

Response = namedtuple('Response',['status_code'])
ident = lambda x:x

class ApiloadTest(unittest.TestCase):

    # Actions

    def setUp(self):

        # Cleanup
        self.addCleanup(patch.stopall)

        # Various patches
        self.requests = patch.object(module, 'requests').start()
        self.request = patch.object(module, 'request').start()
        self.urlfor = patch.object(module, 'url_for').start()
        self.urlfor.return_value = '/api/mock'
        self.jsonpify = patch.object(module, 'jsonpify').start()
        self.jsonpify.side_effect = ident
        module.os_api = 'api'
        module.os_conductor = 'conductor'

    # Tests

    def assertResponse(self, ret, status=None, progress=None, error=None):
        if status is not None:
            self.assertEquals(ret['status'], status)
        if progress is not None:
            self.assertEquals(ret['progress'], progress)
        if error is not None:
            self.assertEquals(ret['error'], error)

    def test___load___good_request(self):
        api_load = module.ApiLoad()
        self.requests.get = Mock(return_value=Response(200))
        self.request.values = {'datapackage':'bla'}
        self.assertResponse(api_load(), 'queued', 0)

    def test___load___bad_request(self):
        api_load = module.ApiLoad()
        self.requests.get = Mock(return_value=Response(200))
        self.request.values = {'datapackaged':'bla'}
        self.assertRaises(BadRequest, api_load)

    def test___callback___server_down(self):
        api_load = module.ApiLoad()
        self.requests.get = Mock(return_value=Response(499))
        self.request.values = {'datapackage':'bla'}
        self.assertResponse(api_load(), 'fail', error='HTTP 499')

    def test___poll___good_request(self):
        api_load = module.ApiLoad()
        self.requests.get = Mock(return_value=Response(200))
        self.request.values = {'datapackage':'bla2'}
        api_load()

        api_poll = module.ApiPoll()
        self.request.values = {'datapackage':'bla2'}
        self.assertResponse(api_poll(), 'queued', 0)

    def test___poll___nonexistent_request(self):
        api_poll = module.ApiPoll()
        self.request.values = {'datapackage':'bla3'}
        self.assertRaises(NotFound, api_poll)

    def test___poll___bad_request(self):
        api_poll = module.ApiPoll()
        self.request.values = {'datapackaged':'bla4'}
        self.assertRaises(BadRequest, api_poll)

    def test___callback___no_update(self):
        # No parameters
        api_callback = module.ApiCallback()
        self.request.values = {'package':'bla4'}
        self.assertEquals(api_callback(), "")

        api_poll = module.ApiPoll()
        self.request.values = {'datapackage':'bla4'}
        self.assertRaises(NotFound, api_poll)

    def test___callback___just_status(self):
        # No parameters
        api_callback = module.ApiCallback()
        self.request.values = {'package':'bla5', 'status':'status1'}
        self.assertEquals(api_callback(), "")

        api_poll = module.ApiPoll()
        self.request.values = {'datapackage':'bla5'}
        self.assertResponse(api_poll(), 'status1', 0)

    def test___callback___progress(self):
        # No parameters
        api_callback = module.ApiCallback()
        self.request.values = {'package':'bla6', 'status':'status2', 'progress':123}
        self.assertEquals(api_callback(), "")

        api_poll = module.ApiPoll()
        self.request.values = {'datapackage':'bla6'}
        self.assertResponse(api_poll(), 'status2', 123)

    def test___callback___errormsg_wrong_status(self):
        # No parameters
        api_callback = module.ApiCallback()
        self.request.values = {'package':'bla7', 'status':'status3', 'progress':123, 'error': 'wtf'}
        self.assertEquals(api_callback(), "")

        api_poll = module.ApiPoll()
        self.request.values = {'datapackage':'bla7'}
        self.assertResponse(api_poll(), 'status3', 123)

    def test___callback___error_good_status(self):
        # No parameters
        api_callback = module.ApiCallback()
        self.request.values = {'package':'bla8', 'status':'fail', 'error':'wtf2'}
        self.assertEquals(api_callback(), "")

        api_poll = module.ApiPoll()
        self.request.values = {'datapackage':'bla8'}
        self.assertResponse(api_poll(), 'fail', 0, 'wtf2')


    #
    # def test___call___good_request(self):
    #     authorize = module.Authorize()
    #     self.assertEqual(json.loads(authorize()), {
    #         'filedata': {
    #             'data/file1': {
    #                 'name': 'file1',
    #                 'length': 100,
    #                 'md5': 'aaa',
    #                 'upload_url': 'http://test.com',
    #                 'upload_query': {'key': ['value']},
    #             },
    #         },
    #     })
    #     self.bucket.new_key.assert_called_with('owner/name/data/file1')
