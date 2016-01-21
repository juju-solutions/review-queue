import datetime
import os
import zipfile

import requests

from pyramid.security import Allow

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
    )

from sqlalchemy.orm import (
    backref,
    relationship,
)

from .base import Base, DBSession
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
    MIN_VOTE = -2
    MAX_VOTE = 2

    user_id = Column(Integer, ForeignKey('user.id'))

    source_url = Column(Text)
    status = Column(Enum(*Status._fields, name='Status'))

    user = relationship('User')
    revisions = relationship('Revision', backref='review')

    @property
    def age(self):
        return datetime.datetime.utcnow() - self.created_at

    @property
    def latest_revision(self):
        #TODO use query instead
        return self.revisions[0]

    def create_tests(self, settings, substrates=None):
        if self.revisions:
            self.revisions[0].create_tests(
                settings, substrates
            )

    def reject(self):
        pass

    def accept(self):
        pass

    def get_diff(self, settings):
        current_revision = self.revisions[0]
        prior_revision = self.revisions[1] if len(self.revisions) > 1 else None
        return current_revision.get_diff(prior_revision, settings)


class RevisionTest(Base):
    revision_id = Column(Integer, ForeignKey('revision.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    status = Column(Text)  # RETRY, PENDING, PASS, FAIL
    substrate = Column(Text)
    url = Column(Text)
    finished = Column(DateTime)

    user = relationship('User')

    def send_ci_request(self, settings):
        test_url = self.revision.get_test_url()
        if not test_url:
            return

        req_url = settings['testing.jenkins_url']
        callback_url = (
            '{}/revision_tests/{}'.format(
                settings['base_url'],
                self.id,
            )
        )

        req_params = {
            'url': test_url,
            'token': settings['testing.jenkins_token'],
            'cause': 'Review Queue Ingestion',
            'callback_url': callback_url,
            'job_id': self.id,
            'envs': self.substrate,
        }

        r = requests.get(req_url, params=req_params)

        if r.status_code == requests.codes.ok:
            self.status = 'PENDING'

    def try_finish(self):
        """Attempt to find a CI result for this ReviewTest
        and update the ReviewTest accordingly.

        Returns True if successful, else False.

        """
        if self.status != 'RUNNING' or not self.url:
            return False

        result_url = '{}artifact/results.json'.format(self.url)
        try:
            result_data = requests.get(result_url).json()
        except:
            return False

        passed = all(
            test.get('returncode', 0) == 0
            for test in result_data.get('tests', {})
        )
        self.status = 'PASS' if passed else 'FAIL'
        self.finished = datetime.datetime.strptime(
            result_data['finished'],
            '%Y-%m-%dT%H:%M:%SZ'
        )

        return True

    def cancel(self):
        self.status = 'CANCELED'
        self.finished = datetime.datetime.utcnow()


class Revision(Base):
    review_id = Column(Integer, ForeignKey('review.id'))

    revision_url = Column(Text)

    tests = relationship('RevisionTest', backref=backref('revision'))
    comments = relationship('Comment', backref=backref('revision'))

    def get_policy_check_for(self, policy_id):
        return (
            DBSession.query(RevisionPolicyCheck)
            .filter_by(revision_id=self.id)
            .filter_by(policy_id=policy_id)
            .first()
        )

    def get_test_url(self):
        return self.revision_url

    def create_tests(self, settings, substrates=None):
        substrates = (
            substrates or
            settings['testing.default_substrates'].split(',')
        )
        revision_tests = []
        # so we can correlate by `created` time later
        batch_time = datetime.datetime.utcnow()
        for substrate in substrates:
            revision_tests.append(RevisionTest(
                status='RETRY',
                substrate=substrate.strip(),
                created_at=batch_time,
            ))
        self.tests.extend(revision_tests)

        for revision_test in revision_tests:
            revision_test.send_ci_request(settings)

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


class User(Base):
    openid_claimed_id = Column(Text)
    nickname = Column(Text)
    fullname = Column(Text)
    email = Column(Text)
    is_charmer = Column(Boolean)

    comments = relationship('Comment')
    reviews = relationship('Review')

    @property
    def __acl__(self):
        return [
            (Allow, self.id, 'edit'),
        ]


class Comment(Base):
    revision_id = Column(Integer, ForeignKey('revision.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    text = Column(Text)
    vote = Column(Integer)

    user = relationship('User')


class Policy(Base):
    description = Column(Text)


class RevisionPolicyCheck(Base):
    revision_id = Column(Integer, ForeignKey('revision.id'))
    policy_id = Column(Integer, ForeignKey('policy.id'))

    status = Column(Integer)

    @property
    def unreviewed(self):
        return self.status in (None, 0)

    @property
    def passing(self):
        return self.status == 1

    @property
    def failing(self):
        return self.status == 2
