import time
import unittest
from importlib import import_module
from elasticsearch import Elasticsearch, NotFoundError

from tests.module.blueprints.config import LOCAL_ELASTICSEARCH

module = import_module('conductor.blueprints.search.controllers')


class SearchTest(unittest.TestCase):

    # Actions

    def setUp(self):

        # Clean index
        self.es = Elasticsearch(hosts=[LOCAL_ELASTICSEARCH])
        try:
            self.es.indices.delete(index='packages')
        except NotFoundError:
            pass
        self.es.indices.create('packages')

    def indexSomeRecords(self, amount):
        for i in range(amount):
            body = {
                'id': True,
                'package': i,
                'model': 'str%s' % i,
                'origin_url': {
                    'name': 'innername'
                }
            }
            self.es.index('packages', 'package', body)
        self.es.indices.flush('packages')

    def indexSomeRealLookingRecords(self, amount):
        for i in range(amount):
            body = {
                'id': 'package-id-%d' % i,
                'package': {
                    'author': 'The one and only author number%d' % (i+1),
                    'title': 'This dataset is number%d' % i
                }
            }
            self.es.index('packages', 'package', body)
        if amount>0:
            self.es.indices.flush('packages')

    def indexSomePrivateRecords(self):
        i = 0
        for owner in ['owner1', 'owner2']:
            for private in [True, False]:
                for loaded in [True, False]:
                    for content in ['cat', 'dog']:
                        body = {
                            'id': '%s-%s-%s-%s' % (owner, private, loaded, content),
                            'package': {
                                'author': 'The one and only author number%d' % (i+1),
                                'title': 'This dataset is number%d, content is %s' % (i, content),
                                'owner': owner,
                                'private': private
                            },
                            'loaded': loaded
                        }
                        self.es.index('packages', 'package', body)
                        i += 1
        self.es.indices.flush('packages')

    # Tests
    def test___search___all_values_and_empty(self):
        self.assertEquals(len(module.search('package', None)), 0)

    def test___search___all_values_and_one_result(self):
        self.indexSomeRecords(1)
        self.assertEquals(len(module.search('package', None)), 1)

    def test___search___all_values_and_two_results(self):
        self.indexSomeRecords(2)
        self.assertEquals(len(module.search('package', None)), 2)

    def test___search___filter_simple_property(self):
        self.indexSomeRecords(10)
        self.assertEquals(len(module.search('package', None, {'model': ['"str7"']})), 1)

    def test___search___filter_numeric_property(self):
        self.indexSomeRecords(10)
        self.assertEquals(len(module.search('package', None, {'package': ["7"]})), 1)

    def test___search___filter_boolean_property(self):
        self.indexSomeRecords(10)
        self.assertEquals(len(module.search('package', None, {'id': ["true"]})), 10)

    def test___search___filter_multiple_properties(self):
        self.indexSomeRecords(10)
        self.assertEquals(len(module.search('package', None, {'model': ['"str6"'], 'package': ["6"]})), 1)

    def test___search___filter_multiple_values_for_property(self):
        self.indexSomeRecords(10)
        self.assertEquals(len(module.search('package', None, {'model': ['"str6"','"str7"']})), 2)

    def test___search___filter_inner_property(self):
        self.indexSomeRecords(7)
        self.assertEquals(len(module.search('package', None, {"origin_url.name": ['"innername"']})), 7)

    def test___search___filter_no_results(self):
        self.assertEquals(len(module.search('package', None, {'model': ['"str6"'], 'package': ["7"]})), 0)

    def test___search___filter_bad_value(self):
        self.assertEquals(module.search('package', None, {'model': ['str6'], 'package': ["6"]}), None)

    def test___search___filter_nonexistent_kind(self):
        self.assertEquals(module.search('box', None, {'model': ['str6'], 'package': ["6"]}), None)

    def test___search___filter_nonexistent_property(self):
        self.assertEquals(module.search('box', None, {'model': ['str6'], 'boxing': ["6"]}), None)

    def test___search___q_param_no_recs_no_results(self):
        self.indexSomeRealLookingRecords(0)
        self.assertEquals(len(module.search('package', None, {'q': ['"author"']})), 0)

    def test___search___q_param_some_recs_no_results(self):
        self.indexSomeRealLookingRecords(2)
        self.assertEquals(len(module.search('package', None, {'q': ['"writer"']})), 0)

    def test___search___q_param_some_recs_some_results(self):
        self.indexSomeRealLookingRecords(2)
        self.assertEquals(len(module.search('package', None, {'q': ['"number1"']})), 2)

    def test___search___empty_anonymous_search(self):
        self.indexSomePrivateRecords()
        recs = module.search('package', None)
        self.assertEquals(len(recs), 4)
        ids = set([r['id'] for r in recs])
        self.assertSetEqual(ids, {'owner1-False-True-cat',
                                  'owner2-False-True-cat',
                                  'owner1-False-True-dog',
                                  'owner2-False-True-dog',
                                  })

    def test___search___empty_authenticated_search(self):
        self.indexSomePrivateRecords()
        recs = module.search('package', 'owner1')
        ids = set([r['id'] for r in recs])
        self.assertSetEqual(ids, {'owner1-False-False-cat',
                                  'owner1-False-True-cat',
                                  'owner1-True-False-cat',
                                  'owner1-True-True-cat',
                                  'owner2-False-True-cat',
                                  'owner1-False-False-dog',
                                  'owner1-False-True-dog',
                                  'owner1-True-False-dog',
                                  'owner1-True-True-dog',
                                  'owner2-False-True-dog',
                                  })
        self.assertEquals(len(recs), 10)

    def test___search___q_param_anonymous_search(self):
        self.indexSomePrivateRecords()
        recs = module.search('package', None, {'q': ['"cat"']})
        self.assertEquals(len(recs), 2)
        ids = set([r['id'] for r in recs])
        self.assertSetEqual(ids, {'owner1-False-True-cat',
                                  'owner2-False-True-cat',
                                  })

    def test___search___q_param_authenticated_search(self):
        self.indexSomePrivateRecords()
        recs = module.search('package', 'owner1', {'q': ['"cat"']})
        ids = set([r['id'] for r in recs])
        self.assertSetEqual(ids, {'owner1-False-False-cat',
                                  'owner1-False-True-cat',
                                  'owner1-True-False-cat',
                                  'owner1-True-True-cat',
                                  'owner2-False-True-cat',
                                  })
        self.assertEquals(len(recs), 5)
