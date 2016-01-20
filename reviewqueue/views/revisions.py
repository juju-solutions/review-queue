from pyramid.httpexceptions import (
    HTTPUnauthorized,
    HTTPFound,
)
from pyramid.security import Allow
from pyramid.security import Everyone
from pyramid.view import view_config

from ..db import DB


def includeme(config):
    config.add_route(
        'test_revision', '/revision/{id}/test',
        factory=RevisionFactory, traverse='/{id}')


class RevisionFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        revision = DB().get_revision(id=key)
        if not revision:
            raise KeyError(
                "No revision with id '%s'" % key)

        revision.__parent__ = self
        revision.__name__ = key
        return revision


@view_config(
    route_name='test_revision',
    permission='view',
)
def revision_test(request):
    """Submit new tests for a Revision

    POST /revision/:id/test

    """
    revision = request.context

    user = request.user
    if not (user and user.is_charmer):
        return HTTPUnauthorized()

    substrate = request.params.get('substrate')
    substrate = (
        request.registry.settings['testing.substrates'].split(',')
        if substrate == 'all'
        else [substrate]
    )

    revision.create_tests(
        request.registry.settings, substrates=substrate)

    return HTTPFound(location=request.route_url(
        'reviews_show', id=revision.review.id))
