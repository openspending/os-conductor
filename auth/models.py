import os
import json
import datetime
from hashlib import md5

from contextlib import contextmanager

from sqlalchemy import DateTime
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Unicode, String, create_engine
from sqlalchemy.orm import sessionmaker

# ## SQL DB
Base = declarative_base()

_sql_engine = None
_sql_session = None


def setup_engine(connection_string):
    global _sql_engine
    _sql_engine = create_engine(connection_string)
    Base.metadata.create_all(_sql_engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    global _sql_session
    if _sql_session is None:
        assert _sql_engine is not None, "No database defined, please set your DATABASE_URL environment variable"
        _sql_session = sessionmaker(bind=_sql_engine)
    session = _sql_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.expunge_all()


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

# ## USERS


class User(Base):
    __tablename__ = 'users'
    id = Column(String(128), primary_key=True)
    provider_id = Column(String(128))
    username = Column(Unicode, unique=True, nullable=False)
    name = Column(Unicode)
    email = Column(Unicode)
    avatar_url = Column(String(512))
    join_date = Column(DateTime)


def get_user(id_):
    with session_scope() as session:
        ret = session.query(User).filter_by(id=id_).first()
        if ret is not None:
            return object_as_dict(ret)
    return None

def get_user_by_username(username_):
    with session_scope() as session:
        ret = session.query(User).filter_by(username=username_).first()
        if ret is not None:
            return object_as_dict(ret)
    return None

def hash_email(email):
    return md5(email.encode('utf8')).hexdigest()


def save_user(user):
    with session_scope() as session:
        user = User(**user)
        session.add(user)


def create_or_get_user(provider_id, name, username, email, avatar_url):
    id_ = hash_email(email)
    user = get_user(id_)
    if user is None:
        document = {
            'id': id_,
            'provider_id': provider_id,
            'username': username,
            'name': name,
            'email': email,
            'avatar_url': avatar_url,
            'join_date': datetime.datetime.now()
        }
        save_user(document)
        return document
    return user
