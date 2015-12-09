import datetime

from pyramid.security import Allow

from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    Integer,
    Text,
    )

from sqlalchemy.orm import (
    relationship,
)

from .base import Base


def make_enum(name, *fields):
    from collections import namedtuple
    return namedtuple(name, fields)(*fields)


Status = make_enum(
    'Status',

    'TESTING',
    'PENDING',
    'REVIEWED',
    'PROMULGATED',
    'CLOSED',
)


class Review(Base):
    MIN_VOTES = -2
    MAX_VOTES = 2

    user_id = Column(Integer, ForeignKey('user.id'))

    source_url = Column(Text)
    status = Column(Enum(*Status._fields, name='Status'))

    user = relationship('User')
    votes = relationship('Vote')

    @property
    def age(self):
        return datetime.datetime.utcnow() - self.created_at

    def start_tests(self, test_environments):
        """Kick off tests for this review.

        Makes http request(s) to a remote jenkins server to initiate tests.
        When the tests finish, our app is called back via http with the
        results.

        """
        for env in test_environments:
            pass

    def reject(self):
        pass

    def accept(self):
        pass


class Vote(Base):
    review_id = Column(Integer, ForeignKey('review.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    vote = Column(Integer)

    review = relationship('Review')
    user = relationship('User')


class User(Base):
    openid_claimed_id = Column(Text)
    nickname = Column(Text)
    fullname = Column(Text)
    email = Column(Text)

    comments = relationship('Comment')
    reviews = relationship('Review')
    votes = relationship('Vote')

    @property
    def __acl__(self):
        return [
            (Allow, self.id, 'edit'),
        ]


class Comment(Base):
    review_id = Column(Integer, ForeignKey('review.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    text = Column(Text)

    review = relationship('Review')
    user = relationship('User')
