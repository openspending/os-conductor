import os
import sys
import logging
import urllib3

from elasticsearch import Elasticsearch, NotFoundError
from os_package_registry import PackageRegistry
from sqlalchemy import MetaData, create_engine

urllib3.disable_warnings()
logging.root.setLevel(logging.INFO)


if __name__ == "__main__":

    es_host = os.environ['OS_ELASTICSEARCH_ADDRESS']
    es = Elasticsearch(hosts=[es_host], use_ssl='https' in es_host)

    target_index = sys.argv[1]

    es.indices.delete_alias(target_index, 'packages')
