import os
import json
import datetime
from hashlib import md5

from sqlalchemy import DateTime
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Unicode, String, create_engine
from sqlalchemy.orm import sessionmaker

# ## SQL DB
Base = declarative_base()

_sql_engine = None


def setup_engine(connection_string):
    global _sql_engine
    _sql_engine = create_engine(connection_string)
    Base.metadata.create_all(_sql_engine)


def _session():
    assert _sql_engine is not None, "No database defined, please set your DATABASE_URL environment variable"
    return sessionmaker(bind=_sql_engine)()


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

# ## USERS


class User(Base):
    __tablename__ = 'users'
    id = Column(String(128), primary_key=True)
    provider_id = Column(String(128))
    username = Column(Unicode)
    name = Column(Unicode)
    email = Column(Unicode)
    avatar_url = Column(String(512))
    join_date = Column(DateTime)


def get_user(id_):
    ret = _session().query(User).filter_by(id=id_).first()
    if ret is not None:
        return object_as_dict(ret)
    return None


def hash_email(email):
    return md5(email.encode('utf8')).hexdigest()


def save_user(user):
    user = User(**user)
    s = _session()
    s.add(user)
    s.commit()


def create_or_get_user(provider_id, name, email, avatar_url):
    id_ = hash_email(email)
    user = get_user(id_)
    if user is None:
        document = {
            'id': id_,
            'provider_id': provider_id,
            'username': None,
            'name': name,
            'email': email,
            'avatar_url': avatar_url,
            'join_date': datetime.datetime.now()
        }
        save_user(document)
        return document
    return user


# ## PERMISSIONS
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


# ## FIXTURES
def load_fixtures():
    if get_permission('*', 'world') is None:
        session = _session()
        glob = Permission(userid='*',
                          service='world',
                          permissions='{"any":true}')
        session.add(glob)
        session.commit()
