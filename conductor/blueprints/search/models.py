import os
import json

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

_engine = None

ENABLED_SEARCHES = {
    'user': {
        'index': 'users',
        'doc_type': 'user_profile',
        '_source': ['idhash', 'name', 'avatar_url', 'datasets']
    },
    'package': {
        'index': 'packages',
        'doc_type': 'package',
        '_source': ['id', 'model', 'package', 'origin_url']
    }
}


def _get_engine():
    global _engine
    if _engine is None:
        es_host = os.environ['OS_ELASTICSEARCH_ADDRESS']
        _engine = Elasticsearch(hosts=[es_host], use_ssl='https' in es_host)
    return _engine


def query(kind, size=100, **kw):
    kind_params = ENABLED_SEARCHES.get(kind)
    if kind_params is None:
        return None
    try:
        # Arguments received from a network request come in kw, as a mapping
        # between param_name and a list of received values.
        # If size was provided by the user, it will be a list, so we take its
        # first item.
        if type(size) is list:
            size = size[0]
        api_params = {'size': int(size)}
        api_params.update(kind_params)

        or_clauses = []
        for k, v_arr in kw.items():
            if k.split('.')[0] in kind_params['_source']:
                filters = ["{0}:{1}".format(k, json.dumps(json.loads(v)))
                           for v in v_arr]
                or_clauses.append("({0})".format(" OR ".join(filters)))
        q_str = " AND ".join(or_clauses)

        if len(q_str) > 0:
            api_params['q'] = q_str
        ret = _get_engine().search(**api_params)
        if ret.get('hits') is not None:
            return [hit['_source'] for hit in ret['hits']['hits']]
    except (NotFoundError, json.decoder.JSONDecodeError, ValueError):
        pass
    return None
