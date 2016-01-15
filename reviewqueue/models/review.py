import datetime
import os
import zipfile

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
from .. import helpers as h


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


class Review(Base):
    MIN_VOTES = -2
    MAX_VOTES = 2

    user_id = Column(Integer, ForeignKey('user.id'))

    source_url = Column(Text)
    status = Column(Enum(*Status._fields, name='Status'))

    user = relationship('User')
    votes = relationship('Vote')
    revisions = relationship('Revision')

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

    def get_diff(self, settings):
        current_revision = self.revisions[0]
        prior_revision = self.revisions[1] if len(self.revisions) > 1 else None
        return current_revision.get_diff(prior_revision, settings)


class Revision(Base):
    review_id = Column(Integer, ForeignKey('review.id'))

    revision_url = Column(Text)

    def archive_url(self, settings):
        revision_url = self.revision_url
        if revision_url.startswith('cs:'):
            revision_url = revision_url[len('cs:'):]

        cs = h.charmstore(settings)
        return cs.archive_url(revision_url)

    def get_diff(self, prior_revision, settings):
        to_dir, from_dir = self.fetch_source(settings), None
        if prior_revision:
            from_dir = prior_revision.fetch_source(settings)

        return h.Diff(from_dir, to_dir)

    def fetch_source(self, settings):
        source_dir = self.get_source_dir(settings)
        if os.path.exists(source_dir):
            return source_dir
        else:
            os.mkdir(source_dir)

        archive_path = h.download_file(
            self.archive_url(settings))
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(source_dir)
        os.unlink(archive_path)

        return source_dir

    def get_source_dir(self, settings):
        root_dir = settings['revision_source_dir']
        return os.path.join(root_dir, str(self.id))


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
