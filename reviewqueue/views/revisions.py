from pyramid.httpexceptions import (
    HTTPUnauthorized,
    HTTPFound,
)
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.security import Everyone
from pyramid.view import view_config

from ..db import DB
from .. import models as M


def includeme(config):
    config.add_route(
        'revision_test', '/revision/{id}/test',
        factory=RevisionFactory, traverse='/{id}')
    config.add_route(
        'revision_comment', '/revision/{id}/comment',
        factory=RevisionFactory, traverse='/{id}')


class RevisionFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, Authenticated, 'comment'),
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
    route_name='revision_test',
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


@view_config(
    route_name='revision_comment',
    permission='comment',
)
def revision_comment(request):
    """Comment/vote on a Revision

    POST /revision/:id/comment

    """
    revision = request.context
    user = request.user
    comment_text = request.params.get('comment')
    vote = int(request.params.get('vote', 0))

    comment = M.Comment(
        text=comment_text,
        vote=vote,
        user=user,
    )
    revision.comments.append(comment)

    return HTTPFound(location=request.route_url(
        'reviews_show', id=revision.review.id))
