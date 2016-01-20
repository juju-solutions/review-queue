from . import helpers as h
from . import models as M


class DB(object):
    def __init__(self):
        self.session = M.DBSession()

    def _get_object(self, klass, **kw):
        return self.session.query(klass) \
            .filter_by(**kw) \
            .first()

    def flush(self):
        self.session.flush()

    def get_review(self, **kw):
        return self._get_object(M.Review, **kw)

    def get_reviews(self):
        return self.session.query(M.Review) \
            .order_by(M.Review.created_at)

    def get_revision(self, **kw):
        return self._get_object(M.Revision, **kw)

    def create_review(self, user, source_url, charmstore_entity, settings):
        revision_urls = charmstore_entity['Meta']['revision-info']['Revisions']
        review = M.Review(
            source_url=source_url,
            status=M.Status.NEEDS_REVIEW,
        )
        user.reviews.append(review)

        # get (at most) the first two revisions
        for i, revision_url in enumerate(revision_urls):
            revision = M.Revision(
                revision_url=revision_url,
            )
            review.revisions.append(revision)
            if i > 0:
                break

        review.create_tests(settings)
        return review

    def vote_on_review(self, review, user, vote):
        if (vote == 0 or vote not in
                range(review.MIN_SCORE,
                      review.MAX_SCORE + 1)):
            return False

        review.votes.append(
            M.Vote(user=user, vote=vote))

        if review.score <= review.MIN_SCORE:
            review.reject()

        if review.score >= review.MAX_SCORE:
            review.accept()

        return True

    def get_user(self, **kw):
        return self._get_object(M.User, **kw)

    def create_user(self, settings, **kw):
        lp = h.get_lp()
        lp_user = lp.load('{}/~{}'.format(
            settings['launchpad.api.url'],
            kw['nickname']),
        )
        kw['is_charmer'] = lp_user in lp.people['charmers'].members

        u = M.User(**kw)
        self.session.add(u)
        return u
