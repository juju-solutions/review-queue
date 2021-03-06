import datetime
import re
import subprocess

from pyramid.security import Allow

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Text,
    )

from sqlalchemy.orm import (
    relationship,
)

from sqlalchemy.ext.orderinglist import ordering_list

from .base import Base, DBSession, Status
from .history_meta import Versioned
from .. import helpers as h


class Review(Versioned, Base):
    MIN_VOTE = -2
    MAX_VOTE = 2

    user_id = Column(Integer, ForeignKey('user.id'))

    source_url = Column(Text)
    description = Column(Text)
    vote = Column(Integer, default=0)
    charm_name = Column(Text)
    channel = Column(Text)
    status = Column(Enum(*Status._fields, name='Status'))
    promulgated = Column(Boolean)
    is_cpp = Column(Boolean)
    is_oil = Column(Boolean)

    user = relationship('User')
    revisions = relationship(
        'Revision',
        backref='review', order_by='Revision._position',
        collection_class=ordering_list('_position'))

    @property
    def __acl__(self):
        return [
            (Allow, self.user.id, 'edit'),
            (Allow, 'charmers', 'edit'),
        ]

    @property
    def revisionless_url(self):
        match = re.match(r'^(.*)-(\d+)$', self.source_url)
        if not match:
            return self.source_url
        return match.group(1)

    @classmethod
    def get_active_reviews(cls):
        return (
            DBSession.query(cls)
            .filter(~cls.status.in_([
                'CLOSED',
            ]))
            .order_by(cls.created_at)
        )

    def icon_url(self, settings):
        cs = h.charmstore(settings)
        return cs.charm_icon_url(self.source_url, channel=self.channel)

    def get_policy_check_for(self, policy_id):
        from .other import ReviewPolicyCheck
        return (
            DBSession.query(ReviewPolicyCheck)
            .filter_by(review_id=self.id)
            .filter_by(policy_id=policy_id)
            .first()
        )

    def get_progress(self):
        """Return a dictionary denoting the progress of the review.

        Example::

            {
                'passing': 4,
                'failing': 5,
                'total': 10,
            }

        Note: Progress is calculated using *required* policy checks only;
        optional policy checks are not included.

        """
        from .other import Policy, ReviewPolicyCheck

        total_count = DBSession.query(Policy).filter_by(required=True).count()
        pass_count = (
            DBSession.query(ReviewPolicyCheck)
            .join(Policy)
            .filter(Policy.required == True)
            .filter(ReviewPolicyCheck.review_id == self.id)
            .filter(ReviewPolicyCheck.status == 1)
            .count()
        )
        fail_count = (
            DBSession.query(ReviewPolicyCheck)
            .join(Policy)
            .filter(Policy.required == True)
            .filter(ReviewPolicyCheck.review_id == self.id)
            .filter(ReviewPolicyCheck.status == 2)
            .count()
        )
        return {
            'passing': pass_count,
            'failing': fail_count,
            'total': total_count,
        }

    @property
    def age(self):
        return datetime.datetime.utcnow() - self.created_at

    @property
    def human_status(self):
        return h.human_status(self.status)

    @property
    def human_vote(self):
        return h.human_vote(self.vote)

    @property
    def latest_revision(self):
        # TODO use query instead
        return self.revisions[0] if self.revisions else None

    def create_tests(self, settings, substrates=None):
        if self.revisions:
            self.latest_revision.create_tests(
                settings, substrates
            )

    def refresh_tests(self, settings):
        for r in self.revisions:
            r.refresh_tests(settings)

    def get_new_revisions(self, settings):
        """Return a list of new revisions for this Review

        """
        cs = h.charmstore(settings)
        charmstore_entity = h.get_charmstore_entity(
            cs, self.source_url, channel=self.channel)
        if not charmstore_entity:
            return []
        remote_revisions = (
            charmstore_entity['Meta']['revision-info']['Revisions'])
        current_revision = self.latest_revision.revision_url
        new_revisions = (
            remote_revisions[0:remote_revisions.index(current_revision)])
        return new_revisions

    def refresh_revisions(self, settings):
        """Check for and download new source revisions for this review.

        """
        cs = h.charmstore(settings)
        charmstore_entity = h.get_charmstore_entity(
            cs, self.source_url,
            channel=self.channel)
        if not charmstore_entity:
            return
        remote_revisions = (
            charmstore_entity['Meta']['revision-info']['Revisions'])
        current_revision = self.latest_revision.revision_url
        if current_revision not in remote_revisions:
            return
        new_revisions = (
            remote_revisions[0:remote_revisions.index(current_revision)])
        if new_revisions:
            from .other import Revision
            for url in reversed(new_revisions):
                self.revisions.insert(0, Revision(revision_url=url))
            self.status = Status.NEEDS_REVIEW
            self.vote = 0
            self.create_tests(settings)

    def reopen(self):
        """Reopen this Review

        """
        self.status = Status.NEEDS_REVIEW

    def close(self):
        """Close this Review

        """
        self.status = Status.CLOSED

    def promulgate(self):
        """Close this Review and promulgate the charm

        """
        if self.promulgated:
            # publish
            cmd = ['charm', 'publish', self.latest_revision.revision_url]
        else:
            # promulgate
            cmd = ['jaas', 'promulgate', self.source_url]

        if subprocess.call(cmd) == 0:
            self.status = Status.PROMULGATED
