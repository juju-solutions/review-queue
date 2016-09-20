from . import helpers as h
from . import models as M


class DB(object):
    def __init__(self):
        self.session = M.DBSession()

    def flush(self):
        self.session.flush()

    def create_review(
            self, user, source_url, description, is_cpp, is_oil,
            charmstore_entity, channel, latest_revision_url, settings):

        promulgated = charmstore_entity['Meta']['promulgated']['Promulgated']
        revision_urls = charmstore_entity['Meta']['revision-info']['Revisions']

        review = M.Review(
            source_url=source_url,
            description=description,
            is_cpp=is_cpp,
            is_oil=is_oil,
            status=M.Status.NEEDS_REVIEW,
            promulgated=promulgated,
            charm_name=(
                charmstore_entity['Meta']['id-name']['Name']),
            channel=channel,
        )
        user.reviews.append(review)

        # get the latest revision
        review.revisions.append(
            M.Revision(revision_url=(
                latest_revision_url or revision_urls[0]))
        )

        if promulgated:
            # get the promulgated revision to diff against
            cs = h.charmstore(settings)
            promulgated_entity = h.get_charmstore_entity(
                cs, 'cs:{}'.format(review.charm_name))
            promulgated_revision_url = (
                promulgated_entity['Id'])
            review.revisions.append(
                M.Revision(revision_url=promulgated_revision_url)
            )

        review.create_tests(settings)
        return review

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
