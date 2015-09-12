from pyramid.httpexceptions import HTTPFound
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.security import Everyone
from pyramid.view import view_config

from ..db import DB


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
def new(request):
    """New Review form

    GET /reviews/new

    """
    return {}


@view_config(
    route_name='reviews_create',
    permission='create',
)
def create(request):
    """Create New Review

    POST /reviews/create

    """
    db = DB()
    db.create_review(
        request.user,
        source_url=request.params['source_url'],
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
    return {
        'review': review,
    }
