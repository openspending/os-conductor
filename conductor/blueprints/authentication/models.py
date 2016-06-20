import os
import datetime
from hashlib import md5

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

USER_FIELDS = ['id', 'name', 'email', 'avatar_url',
               'datasets', 'idhash', 'username', 'join_date']
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        es_host = os.environ['OS_ELASTICSEARCH_ADDRESS']
        _engine = Elasticsearch(hosts=[es_host], use_ssl='https' in es_host)
    return _engine


def get_user(idhash):
    try:
        ret = _get_engine().get(index="users", doc_type="user_profile",
                                id=idhash, _source=USER_FIELDS)
        if ret['found']:
            return ret['_source']
        return None
    except NotFoundError:
        return None


def hash_email(email):
    return md5(email.encode('utf8')).hexdigest()


def save_user(user):
    idhash = user['idhash']
    _get_engine().index(index="users", doc_type="user_profile",
                        id=idhash, body=user)
    _get_engine().indices.flush(index="users")


def create_or_get_user(userid, name, email, avatar_url):
    idhash = hash_email(email)
    user = get_user(idhash)
    if user is None:
        # TODO: Support a list of emails from the provider,
        # and try to find one account that matches any of them
        document = {
            'id': userid,
            'name': name,
            'email': email,
            'avatar_url': avatar_url,
            'idhash': idhash,
            'username': None,
            'join_date': datetime.datetime.now().isoformat()
        }
        save_user(document)
        return document
    return user
