import datetime
import logging
import os
import zipfile

import requests

from pyramid.security import Allow
from pyramid.renderers import render

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func,
    and_
    )

from sqlalchemy.orm import (
    backref,
    relationship,
)

from sqlalchemy.dialects.postgresql import JSONB

from .base import Base, DBSession, Status
from .. import helpers as h

log = logging.getLogger(__name__)


class Vote(object):
    ACCEPT = 2
    APPROVE = 1
    ABSTAIN = 0
    DISAPPROVE = -1
    REJECT = -2


class RevisionTest(Base):
    revision_id = Column(Integer, ForeignKey('revision.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    status = Column(Text)  # RETRY, PENDING, PASS, FAIL
    substrate = Column(Text)
    url = Column(Text)
    results = Column(JSONB)
    finished = Column(DateTime)

    user = relationship('User')

    def send_ci_request(self, settings):
        if not (settings.get('testing.jenkins_url') or '').strip():
            # Don't try to submit a test unless we have a jenkins_url
            log.warn(
                'Skipping test submission, no value for '
                'testing.jenkins_url in .ini file.')
            return

        if not (settings.get('base_url') or '').strip():
            # Don't submit a test unless we have a base_url since
            # we'd never get the result of the test back anyway
            # (which would lead to a never-ending cycle of retries).
            log.warn(
                'Skipping test submission, no value for '
                'base_url in .ini file.')
            return

        test_url = self.revision.get_test_url()
        if not test_url:
            return

        if not self.id:
            DBSession.flush()

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

        if r.status_code in (200, 201):
            self.status = 'PENDING'

        self.updated_at = datetime.datetime.utcnow()

    def try_finish(self):
        """Attempt to find a CI result for this ReviewTest
        and update the ReviewTest accordingly. Download and store
        result json.

        Returns True if successful, else False.

        """
        if not self.url:
            return False

        result_url = '{}artifact/results.json'.format(self.url)
        try:
            self.results = requests.get(result_url).json()
        except Exception as e:
            log.exception(
                "Couldn't get test results from %s: %s", result_url, e)
            return False

        passed = all(
            test.get('returncode', 0) == 0
            for test in self.results.get('tests', {})
        )
        self.status = 'PASS' if passed else 'FAIL'
        self.finished = datetime.datetime.strptime(
            self.results['finished'],
            '%Y-%m-%dT%H:%M:%SZ'
        )

        return True

    def cancel(self):
        self.status = 'CANCELED'
        self.finished = datetime.datetime.utcnow()


class Revision(Base):
    review_id = Column(Integer, ForeignKey('review.id'))

    revision_url = Column(Text)
    _position = Column(Integer)

    tests = relationship('RevisionTest', backref=backref('revision'))
    comments = relationship('Comment', backref=backref('revision'))
    diff_comments = relationship('DiffComment', backref=backref('revision'))

    @property
    def shortname(self):
        return self.revision_url.split('/')[-1]

    @property
    def prior(self):
        return (
            DBSession.query(Revision)
            .filter_by(review_id=self.review.id)
            .filter_by(_position=self._position + 1)
            .first()
        )

    def add_comment(self, comment):
        self.comments.append(comment)

        if comment.vote == Vote.REJECT:
            self.review.vote = -1
        else:
            self.review.vote += comment.vote

        if comment.vote < 0 and self.review.vote < 0:
            self.review.status = Status.NEEDS_FIXING

        if comment.vote > 1 or self.review.vote > 1:
            self.review.status = Status.APPROVED

    def get_test_url(self):
        return self.revision_url

    def get_tests_for_retry(self):
        return (
            DBSession.query(RevisionTest)
            .filter_by(revision_id=self.id)
            .filter_by(status='RETRY')
        )

    def get_tests_missing_results(self):
        """Return RevisionTests that have a 'finished' timestamp,
        but no results json.

        """
        return (
            DBSession.query(RevisionTest)
            .filter_by(revision_id=self.id)
            .filter(RevisionTest.finished != None)  # noqa
            .filter(func.jsonb_typeof(RevisionTest.results) == 'null')
        )

    def get_tests_overdue(self, timeout):
        tests = (
            DBSession.query(RevisionTest)
            .filter_by(revision_id=self.id)
            .filter(RevisionTest.status.in_([
                'PENDING',
                'RUNNING']))
        )

        now = datetime.datetime.utcnow()
        return [
            t for t in tests
            if (now - (t.updated_at or t.created_at)).total_seconds() > timeout
        ]

    def refresh_tests(self, settings):
        for t in self.get_tests_for_retry():
            t.send_ci_request(settings)

        timeout = int(settings.get(
            'testing.timeout', 60 * 60 * 24))
        for t in self.get_tests_overdue(timeout):
            if t.status == 'RUNNING':
                if t.try_finish():
                    continue
            t.send_ci_request(settings)

        for t in self.get_tests_missing_results():
            t.try_finish()

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

    def get_diff(self, settings, prior_revision=None):
        if not prior_revision:
            prior_revision = (
                self.review.revisions[-1]
                if self.review.promulgated else None)

        to_dir, from_dir = self.fetch_source(settings), None
        if prior_revision:
            from_dir = prior_revision.fetch_source(settings)

        return h.Diff(
            from_dir, to_dir,
            prior_revision.get_source_dir(settings)
            if prior_revision else None,
            self.get_source_dir(settings),
        )

    def fetch_source(self, settings):
        source_dir = self.get_source_dir(settings)

        # If we don't have a source dir for this revision, make one
        if not os.path.exists(source_dir):
            os.mkdir(source_dir)

        # If the source dir has contents, that means we've already
        # fetched the source for this revision and can return now
        if os.listdir(source_dir):
            return source_dir

        # We don't have the source for this revision yet - fetch it
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

    def get_groups(self, settings):
        lp = h.get_lp()
        lp_user = lp.load('{}/~{}'.format(
            settings['launchpad.api.url'],
            self.nickname),
        )
        groups = [t.name for t in (lp_user.super_teams or [])]
        groups.append(self.nickname)
        return groups


class Comment(Base):
    revision_id = Column(Integer, ForeignKey('revision.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    text = Column(Text)
    vote = Column(Integer)

    user = relationship('User')

    @property
    def human_vote(self):
        return h.human_vote(self.vote)

    def html(self, request):
        return render(
            'emails/comment.mako', dict(comment=self), request=request)

    def email(self, request):
        settings = request.registry.settings
        sendgrid_api_key = (
            os.environ.get("SENDGRID_APIKEY") or
            settings.get('sendgrid.api_key'))

        recipients = {
            c.user.email
            for rev in self.revision.review.revisions
            for c in rev.comments
            if c.user != self.user
        }
        recipients.add(self.revision.review.user.email)
        if not recipients:
            return

        msg = {
            'to': recipients,
            'from': settings.get('mail.default_sender'),
            'subject': 'Comment on {} review'.format(
                self.revision.review.source_url),
            'html': self.html(request),
        }
        if sendgrid_api_key:
            return h.sendgrid_email(msg, sendgrid_api_key)
        elif settings.get('mail.host'):
            return h.smtp_email(msg, request)
        else:
            log.warn('Email not configured, skipping email notifications.')


class DiffComment(Base):
    revision_id = Column(Integer, ForeignKey('revision.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    text = Column(Text)
    line_start = Column(Integer)
    filename = Column(Text)

    user = relationship('User')


class PolicyCategory(Base):
    name = Column(Text)

    policies = relationship('Policy', backref='category')

    def get_review_policies(self, review):
        return (
            DBSession.query(Policy, ReviewPolicyCheck)
            .outerjoin(
                ReviewPolicyCheck,
                and_(
                    ReviewPolicyCheck.policy_id == Policy.id,
                    ReviewPolicyCheck.review_id == review.id))
            .filter(Policy.category_id == self.id)
            .order_by(Policy.id)
        )


class Policy(Base):
    category_id = Column(Integer, ForeignKey('policycategory.id'))

    description = Column(Text)
    tip = Column(Text)
    required = Column(Boolean)


class ReviewPolicyCheck(Base):
    review_id = Column(Integer, ForeignKey('review.id'))
    revision_id = Column(Integer, ForeignKey('revision.id'))
    policy_id = Column(Integer, ForeignKey('policy.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    status = Column(Integer)

    user = relationship('User')
    revision = relationship('Revision')

    @property
    def unreviewed(self):
        return self.status in (None, 0)

    @property
    def passing(self):
        return self.status == 1

    @property
    def failing(self):
        return self.status == 2
