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
        factory=ReviewFactory, traverse='/{id}')


class ReviewFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, Authenticated, 'create'),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        review = DB().get_review(id=key)
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
    db = DB()

    return {
        'reviews': db.get_reviews(),
    }


@view_config(
    route_name='reviews_new',
    renderer='reviews/new.mako',
    permission='create',
)
def new(request, errors=None):
    """New Review form

    GET /reviews/new

    """
    return {
        'errors': errors,
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
    description = request.params.get('description')

    cs = h.charmstore(request.registry.settings)
    try:
        charmstore_entity = h.get_charmstore_entity(cs, source_url)
    except EntityNotFound:
        return render_to_response(
            'reviews/new.mako',
            new(request, errors=['EntityNotFound']),
            request=request)

    db = DB()
    db.create_review(
        request.user,
        source_url,
        description,
        charmstore_entity,
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

    db = DB()
    revision_id = request.params.get('revision')
    revision = (
        db.get_revision(
            id=int(revision_id),
            review_id=review.id) or review.latest_revision
        if revision_id else review.latest_revision)

    diff_revision_id = request.params.get('diff_revision')
    diff_revision = (
        db.get_revision(
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
        'policy_checklist': M.DBSession.query(M.Policy),
    }
