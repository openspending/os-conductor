import os

from elasticsearch import Elasticsearch

from os_package_registry import PackageRegistry

# ## ElasticSearch
_es_engine = None

PACKAGES_INDEX_NAME = os.environ.get('OS_ES_PACKAGES_INDEX_NAME', 'packages')


def _get_es_engine():
    global _es_engine
    if _es_engine is None:
        es_host = os.environ['OS_ELASTICSEARCH_ADDRESS']
        _es_engine = Elasticsearch(hosts=[es_host], use_ssl='https' in es_host)
    return _es_engine


package_registry = PackageRegistry(es_instance=_get_es_engine(),
                                   index_name=PACKAGES_INDEX_NAME)
