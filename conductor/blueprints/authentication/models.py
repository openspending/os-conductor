import os

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Unicode, String, create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Unicode, primary_key=True)
    name = Column(Unicode)
    email = Column(Unicode)
    avatar_url = Column(String)


_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(os.environ['OS_CONDUCTOR_ENGINE'])
    return _engine


def _session():
    return sessionmaker(bind=_get_engine())()


def get_user(userid):
    return _session().query(User).filter(User.id == userid).first()


def create_or_get_user(userid, name, email, avatar_url):
    session = _session()
    user = session.query(User).filter(User.id == userid).first()
    if user is not None:
        return user
    user = User(id=userid, name=name, email=email, avatar_url=avatar_url)
    session.add(user)
    session.commit()
    return user


Base.metadata.create_all(_get_engine())
