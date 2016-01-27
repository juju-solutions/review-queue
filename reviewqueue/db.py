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
            promulgated=(
                charmstore_entity['Meta']['promulgated']['Promulgated']),
            charm_name=(
                charmstore_entity['Meta']['id-name']['Name']),
        )
        user.reviews.append(review)

        # get the latest revision
        review.revisions.append(
            M.Revision(revision_url=revision_urls[0])
        )

        if review.promulgated:
            # get the promulgated revision to diff against
            cs = h.charmStore(settings)
            promulgated_entity = h.get_charmstore_entity(
                cs, 'cs:{}'.format(review.charm_name))
            promulgated_revision_url = (
                promulgated_entity['Meta']['revision-info']['Revisions'][0])
            review.revisions.append(
                M.Revision(revision_url=promulgated_revision_url)
            )

        review.create_tests(settings)
        return review

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
