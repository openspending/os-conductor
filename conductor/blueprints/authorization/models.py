import os
import json

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Unicode, String, create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Permission(Base):
    __tablename__ = 'permissions'
    userid = Column(Unicode, primary_key=True)
    service = Column(Unicode, primary_key=True)
    permissions = Column(Unicode)


_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(os.environ['OS_CONDUCTOR_ENGINE'])
    return _engine


def _session():
    return sessionmaker(bind=_get_engine())()


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


Base.metadata.create_all(_get_engine())

# Create some fixtures:
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
