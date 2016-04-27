import datetime
import subprocess

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

    user = relationship('User')
    revisions = relationship(
        'Revision',
        backref='review', order_by='Revision._position',
        collection_class=ordering_list('_position'))

    @classmethod
    def get_active_reviews(cls):
        return (
            DBSession.query(cls)
            .filter(~cls.status.in_([
                'CLOSED',
            ]))
        )

    def get_policy_check_for(self, policy_id):
        from .other import ReviewPolicyCheck
        return (
            DBSession.query(ReviewPolicyCheck)
            .filter_by(review_id=self.id)
            .filter_by(policy_id=policy_id)
            .first()
        )

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

    def refresh_revisions(self, settings):
        """Check for and download new source revisions for this review.

        """
        cs = h.charmstore(settings)
        charmstore_entity = h.get_charmstore_entity(
            cs, self.source_url,
            channel=self.channel)
        remote_revisions = (
            charmstore_entity['Meta']['revision-info']['Revisions'])
        current_revision = self.latest_revision.revision_url
        new_revisions = (
            remote_revisions[0:remote_revisions.index(current_revision)])
        if new_revisions:
            from .other import Revision
            for url in reversed(new_revisions):
                self.revisions.insert(0, Revision(revision_url=url))
            self.status = Status.NEEDS_REVIEW
            self.vote = 0
            self.create_tests(settings)

    def close(self):
        """Close this Review

        """
        self.status = 'CLOSED'

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
            self.status = 'PROMULGATED'
