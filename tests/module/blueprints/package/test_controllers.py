from collections import namedtuple
import unittest

import time

import jwt
from elasticsearch import Elasticsearch, NotFoundError
from os_package_registry import PackageRegistry
from ..config import LOCAL_ELASTICSEARCH
from werkzeug.exceptions import BadRequest, NotFound, Forbidden

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
from importlib import import_module

from conductor.blueprints.user.controllers import PRIVATE_KEY

module = import_module('conductor.blueprints.package.controllers')
Response = namedtuple('Response', ['status_code'])
_cache = {}
callback = 'http://conductor/callback'
token = jwt.encode({}, PRIVATE_KEY, algorithm='RS256').decode('ascii')


def cache_get(key):
    global _cache
    return _cache.get(key)


def cache_set(key, value, timeout):
    global _cache
    _cache[key] = value


class ApiloadTest(unittest.TestCase):

    # Actions

    def setUp(self):

        # Cleanup
        self.addCleanup(patch.stopall)

        # Various patches
        self.requests = patch.object(module, 'requests').start()
        module.os_api = 'api'
        module.os_conductor = 'conductor'

        global _cache
        _cache = {}

    # Tests

    def assertResponse(self, ret, status=None, progress=None, error=None):
        if status is not None:
            self.assertEquals(ret['status'], status)
        if progress is not None:
            self.assertEquals(ret['progress'], progress)
        if error is not None:
            self.assertEquals(ret['error'], error)

    def test___load___good_request(self):
        api_load = module.upload
        self.requests.get = Mock(return_value=Response(200))
        self.assertResponse(api_load('bla', callback, token, cache_set), 'queued', 0)

    # def test___load___bad_request(self):
    #     api_load = module.upload
    #     self.requests.get = Mock(return_value=Response(200))
    #     self.assertRaises(BadRequest, api_load, None, callback, token, cache_set)
    #
    # def test___load___unauthorized_request(self):
    #     api_load = module.upload
    #     self.requests.get = Mock(return_value=Response(200))
    #     self.assertRaises(Forbidden, api_load, 'bla', callback, None, cache_set)

    def test___callback___server_down(self):
        api_load = module.upload
        self.requests.get = Mock(return_value=Response(499))
        self.assertResponse(api_load('bla', callback, token, cache_set), 'fail', error='HTTP 499')

    def test___poll___good_request(self):
        api_load = module.upload
        self.requests.get = Mock(return_value=Response(200))
        api_load('bla2', callback, token, cache_set)

        api_poll = module.upload_status
        self.assertResponse(api_poll('bla2', cache_get), 'queued', 0)

    def test___poll___nonexistent_request(self):
        api_poll = module.upload_status
        self.assertEquals(api_poll('bla3', cache_get), None)

    # def test___poll___bad_request(self):
    #     api_poll = module.upload_status
    #     self.assertRaises(BadRequest, api_poll, None, cache_get)

    def test___callback___no_update(self):
        # No parameters
        api_callback = module.upload_status_update
        self.assertEquals(api_callback('bla4', None, None, 0, cache_get, cache_set), None)

        api_poll = module.upload_status
        self.assertEquals(api_poll('bla4', cache_get), None)

    def test___callback___just_status(self):
        # No parameters
        api_callback = module.upload_status_update
        self.assertEquals(api_callback('bla5', 'status1', None, 0, cache_get, cache_set), None)

        api_poll = module.upload_status
        self.assertResponse(api_poll('bla5', cache_get), 'status1', 0)

    def test___callback___progress(self):
        # No parameters
        api_callback = module.upload_status_update
        self.assertEquals(api_callback('bla6', 'status2', None, 123, cache_get, cache_set), None)

        api_poll = module.upload_status
        self.assertResponse(api_poll('bla6', cache_get), 'status2', 123)

    def test___callback___errormsg_wrong_status(self):
        # No parameters
        api_callback = module.upload_status_update
        self.assertEquals(api_callback('bla7', 'status3', 'wtf', 123, cache_get, cache_set), None)

        api_poll = module.upload_status
        self.assertResponse(api_poll('bla7', cache_get), 'status3', 123)

    def test___callback___error_good_status(self):
        # No parameters
        api_callback = module.upload_status_update
        self.assertEquals(api_callback('bla8', 'fail', 'wtf8', 0, cache_get, cache_set), None)

        api_poll = module.upload_status
        self.assertResponse(api_poll('bla8', cache_get), 'fail', 0, 'wtf8')


class PublishAPITests(unittest.TestCase):

    def setUp(self):
        # Clean index
        self.es = Elasticsearch(hosts=[LOCAL_ELASTICSEARCH])
        try:
            self.es.indices.delete(index='users')
        except NotFoundError:
            pass
        self.es.indices.create('users')
        time.sleep(1)

        self.pr = PackageRegistry(es_connection_string=LOCAL_ELASTICSEARCH)
        self.pr.save_model('name','datapackage_url',{},{},'dataset','author')

    def test__initial_value__none(self):
        pkg = self.pr.get_package('name')
        assert(pkg.get('private') is None)

    def test__toggle__published(self):
        module.toggle_publish('name', token, toggle=True)
        pkg = self.pr.get_package('name')
        assert(pkg.get('private') is True)

    def test__toggle_twice__not_published(self):
        module.toggle_publish('name', token, toggle=True)
        module.toggle_publish('name', token, toggle=True)
        pkg = self.pr.get_package('name')
        assert(pkg.get('private') is False)

    def test__force_publish_initial__correct(self):
        module.toggle_publish('name', token, publish=True)
        pkg = self.pr.get_package('name')
        assert(pkg.get('private') is False)

    def test__force_publish__correct(self):
        module.toggle_publish('name', token, toggle=True)
        module.toggle_publish('name', token, publish=True)
        pkg = self.pr.get_package('name')
        assert(pkg.get('private') is False)

    def test__force_unpublish_initial__correct(self):
        module.toggle_publish('name', token, publish=False)
        pkg = self.pr.get_package('name')
        assert(pkg.get('private') is True)

    def test__force_unpublish__correct(self):
        module.toggle_publish('name', token, toggle=True)
        module.toggle_publish('name', token, toggle=True)
        module.toggle_publish('name', token, publish=False)
        pkg = self.pr.get_package('name')
        assert(pkg.get('private') is True)