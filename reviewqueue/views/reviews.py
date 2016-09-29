import re

from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render_to_response
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.security import Everyone
from pyramid.view import view_config

from theblues.errors import EntityNotFound

from ..db import DB
from .. import models as M
from .. import helpers as h


def includeme(config):
    config.add_route(
        'reviews_index', '/reviews', factory=ReviewFactory)
    config.add_route(
        'reviews_new', '/reviews/new', factory=ReviewFactory)
    config.add_route(
        'reviews_create', '/reviews/create', factory=ReviewFactory)
    config.add_route(
        'reviews_show', '/reviews/{id}',
        factory=ReviewFactory, traverse='/{id}', request_method="GET")
    config.add_route(
        'review_update', '/reviews/{id}',
        factory=ReviewFactory, traverse='/{id}', request_method="POST")
    config.add_route(
        'review_show_import', '/reviews/{id}/import',
        factory=ReviewFactory, traverse='/{id}', request_method="GET")
    config.add_route(
        'review_new_import', '/reviews/{id}/import',
        factory=ReviewFactory, traverse='/{id}', request_method="POST")


class ReviewFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, Authenticated, 'create'),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        review = M.Review.get(key)
        if not review:
            raise KeyError(
                "No review with id '%s'" % key)

        review.__parent__ = self
        review.__name__ = key
        return review


@view_config(
    route_name='reviews_index',
    renderer='reviews/index.mako',
    permission='view',
)
def index(request):
    """Reviews index page

    GET /reviews

    """
    return {
        'reviews': M.Review.get_active_reviews(),
    }


@view_config(
    route_name='reviews_new',
    renderer='reviews/new.mako',
    permission='create',
)
def new(request, validation_result=None):
    """New Review form

    GET /reviews/new

    """
    return {
        'validation_result': validation_result,
    }


def validate(source_url, user, settings):
    """Validate a Review Submission

    POST /reviews/validate

    Validation logic:

    Parse url, get revision number if there is one
    Look up url in charmstore
        If not found, error (prompt to check perms)

    If charm owner not in user's groups, and user not in ~charmers:
        Error, can only submit your own charms for review

    If no revision specified:
        If promulgated, use edge channel
            Re-pull from edge channel
        If not promulgated, use stable channel

    If (revision specified in original url and \
            revision not latest on channel):
        If not promulgated:
            Must review latest, prompt to accept
        If promulgated:
            Acceptable, but prompt with option to use latest
    else:
        Prompt to confirm revision/channel

    """
    match = re.match(r'^(.*)-(\d+)$', source_url)
    revision_number = match.group(2) if match else None

    cs = h.charmstore(settings)
    try:
        charmstore_entity = h.get_charmstore_entity(cs, source_url)
    except EntityNotFound:
        return {
            'error': 'NotFound',
            'source_url': source_url,
        }

    charm_owner = charmstore_entity['Meta']['owner']['User']
    if (charm_owner not in
            user.get_groups(settings) and
            not user.is_charmer):
        return {
            'error': 'NotOwner',
            'owner': charm_owner,
            'source_url': source_url,
        }

    promulgated = charmstore_entity['Meta']['promulgated']['Promulgated']
    if not revision_number:
        if promulgated:
            channel = 'edge'
            charmstore_entity = h.get_charmstore_entity(
                cs, source_url, channel=channel)
        else:
            channel = 'stable'

        latest_revision_url = (
            charmstore_entity['Meta']['revision-info']['Revisions'][0])
        return {
            'location': 'tip',
            'source_url': source_url,
            'channel': channel,
            'promulgated': promulgated,
            'charmstore_entity': charmstore_entity,
            'latest': True,
            'latest_revision_url': None,
        }
    else:
        all_revisions = charmstore_entity['Meta']['revision-info']['Revisions']
        latest_revision_url = all_revisions[0]
        match = re.match(r'^(.*)-(\d+)$', latest_revision_url)
        latest_revision = match.group(2)
        if revision_number != latest_revision:
            if not promulgated:
                return {
                    'error': 'NotLatestRevision',
                    'source_url': source_url,
                    'latest_revision_url': latest_revision_url,
                }
            else:
                for rev in all_revisions[1:]:
                    match = re.match(r'^(.*)-(\d+)$', rev)
                    if match and revision_number == match.group(2):
                        latest_revision_url = rev
                        break

        return {
            'location': 'revision',
            'source_url': source_url,
            'channel': None,
            'promulgated': promulgated,
            'charmstore_entity': charmstore_entity,
            'latest': revision_number != latest_revision,
            'latest_revision_url': latest_revision_url,
        }


@view_config(
    route_name='reviews_create',
    permission='create',
    request_method='POST',
)
def create(request):
    """Create New Review

    POST /reviews/create

    """
    source_url = request.params['source_url']
    if source_url.startswith('cs:'):
        source_url = source_url[len('cs:'):]

    description = request.params.get('description')

    result = validate(source_url, request.user, request.registry.settings)

    if 'error' in result:
        return render_to_response(
            'reviews/new.mako',
            new(request, validation_result=result),
            request=request)

    db = DB()
    db.create_review(
        request.user,
        source_url,
        description,
        request.params.get('cpp', False),
        request.params.get('oil', False),
        result['charmstore_entity'],
        result['channel'],
        result['latest_revision_url'],
        request.registry.settings,
    )
    return HTTPFound(location=request.route_url('reviews_index'))


@view_config(
    route_name='reviews_show',
    renderer='reviews/show.mako',
    permission='view',
)
def show(request):
    """Show Review detail page

    GET /reviews/:id

    """
    review = request.context

    revision_id = request.params.get('revision')
    revision = (
        M.Revision.get(
            id=int(revision_id),
            review_id=review.id) or review.latest_revision
        if revision_id else review.latest_revision)

    diff_revision_id = request.params.get('diff_revision')
    diff_revision = (
        M.Revision.get(
            id=int(diff_revision_id),
            review_id=review.id)
        if diff_revision_id else None)

    substrates = request.registry.settings.get('testing.substrates', '')
    substrates = [s.strip() for s in substrates.split(',')]
    return {
        'review': review,
        'revision': revision,
        'diff_revision': diff_revision,
        'substrates': substrates,
        'policy_categories': M.DBSession.query(M.PolicyCategory),
    }


@view_config(
    route_name='review_update',
    permission='edit',
)
def update(request):
    """Update a Review

    Specifically, Close or Promulgate a review.

    POST /reviews/:id

    """
    review = request.context
    action = request.params.get('action')
    getattr(review, action)()

    return HTTPFound(location=request.route_url('reviews_index'))


@view_config(
    route_name='review_show_import',
    renderer='reviews/show_import.mako',
    permission='edit',
)
def show_import(request):
    """Show form for importing new revisions.

    GET /reviews/:id/import

    """
    review = request.context

    return {
        'review': review,
        'new_revisions': review.get_new_revisions(request.registry.settings),
    }


@view_config(
    route_name='review_new_import',
    permission='edit',
)
def new_import(request):
    """Import a new Revision into a Review

    GET /reviews/:id/import

    """
    review = request.context
    revision = request.params['revision']

    review.revisions.insert(0, M.Revision(revision_url=revision))
    review.status = M.Status.NEEDS_REVIEW
    review.vote = 0
    review.create_tests(request.registry.settings)

    return HTTPFound(location=request.route_url(
        'reviews_show', id=review.id))
