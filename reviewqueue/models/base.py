import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    )

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from zope.sqlalchemy import ZopeTransactionExtension

from .history_meta import versioned_session

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
versioned_session(DBSession)


def make_enum(name, *fields):
    from collections import namedtuple
    return namedtuple(name, fields)(*fields)


Status = make_enum(
    'Status',

    'NEEDS_REVIEW',
    'NEEDS_FIXING',
    'APPROVED',
    'PROMULGATED',
    'CLOSED',
)


class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=sa.func.now())
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

    def update(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    @classmethod
    def get(cls, *args, **kw):
        if args:
            return DBSession.query(cls).get(*args)

        return (
            DBSession.query(cls)
            .filter_by(**kw)
            .first()
        )


Base = declarative_base(cls=Base)
