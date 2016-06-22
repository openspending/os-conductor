import os
import json
import datetime
from hashlib import md5

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Unicode, String, create_engine
from sqlalchemy.orm import sessionmaker

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError


# ## ElasticSearch
_es_engine = None


def _get_es_engine():
    global _es_engine
    if _es_engine is None:
        es_host = os.environ['OS_ELASTICSEARCH_ADDRESS']
        _es_engine = Elasticsearch(hosts=[es_host], use_ssl='https' in es_host)
    return _es_engine


# ## SQL DB
_sql_engine = None


def _get_sql_engine():
    global _sql_engine
    if _sql_engine is None:
        _sql_engine = create_engine(os.environ['OS_CONDUCTOR_ENGINE'])
    return _sql_engine


def _session():
    return sessionmaker(bind=_get_sql_engine())()


# ## USERS

USER_FIELDS = ['id', 'name', 'email', 'avatar_url',
               'datasets', 'idhash', 'username', 'join_date']


def get_user(idhash):
    try:
        ret = _get_es_engine().get(index="users", doc_type="user_profile",
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
    _get_es_engine().index(index="users", doc_type="user_profile",
                           id=idhash, body=user)
    _get_es_engine().indices.flush(index="users")


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

# ## PERMISSIONS
Base = declarative_base()


class Permission(Base):
    __tablename__ = 'permissions'
    userid = Column(Unicode, primary_key=True)
    service = Column(Unicode, primary_key=True)
    permissions = Column(Unicode)


def get_permission(userid, service):
    rec = _session().query(Permission)\
                    .filter(Permission.userid == userid,
                            Permission.service == service)\
                    .first()
    if rec is not None:
        try:
            return json.loads(rec.permissions)
        except json.JSONDecodeError:
            pass
    return None


Base.metadata.create_all(_get_sql_engine())


# ## FIXTURES

if get_permission('google:109637468373886238649', 'sample') is None:
    session = _session()
    user = Permission(userid='google:109637468373886238649',
                      service='sample',
                      permissions='{"moshe":[1,2,3]}')
    session.add(user)
    session.commit()
if get_permission('*', 'sample') is None:
    session = _session()
    glob = Permission(userid='*',
                      service='sample',
                      permissions='{"david":[4,5,6]}')
    session.add(glob)
    session.commit()
if get_permission('*', 'os.datastore') is None:
    session = _session()
    glob = Permission(userid='*',
                      service='os.datastore',
                      permissions='{"datapackage-upload":true}')
    session.add(glob)
    session.commit()
