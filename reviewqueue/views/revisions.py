from pyramid.httpexceptions import (
    HTTPUnauthorized,
    HTTPFound,
    HTTPOk,
)
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.security import Everyone
from pyramid.view import view_config

from .. import models as M
from .. import helpers as h


def includeme(config):
    config.add_route(
        'revision_test', '/revisions/{id}/test',
        factory=RevisionFactory, traverse='/{id}')
    config.add_route(
        'revision_comment', '/revisions/{id}/comment',
        factory=RevisionFactory, traverse='/{id}')
    config.add_route(
        'revision_diff_comment', '/revisions/{id}/diff_comment',
        factory=RevisionFactory, traverse='/{id}')
    config.add_route(
        'revision_policy', '/revisions/{id}/policy',
        factory=RevisionFactory, traverse='/{id}')


class RevisionFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, Authenticated, 'comment'),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        revision = M.Revision.get(key)
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

    POST /revisions/:id/test

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

    POST /revisions/:id/comment

    """
    revision = request.context
    user = request.user
    comment_text = request.params.get('comment')
    status = request.params.get('status')
    vote = int(request.params.get('vote', 0))
    if revision.review.user == user:
        # user can't vote on their own review
        vote = 0

    comment = M.Comment(
        text=comment_text,
        vote=vote,
        user=user,
    )
    revision.add_comment(comment)
    if status:
        revision.review.status = status

    return HTTPFound(location=request.route_url(
        'reviews_show', id=revision.review.id))


@view_config(
    route_name='revision_diff_comment',
    permission='comment',
    renderer='json',
)
def revision_diff_comment(request):
    """Comment/vote on a line of a Revision file diff

    POST /revisions/:id/diff_comment

    """
    revision = request.context
    comment_text = request.params.get('comment')
    line_start = int(request.params.get('line_start'))
    filename = request.params.get('filename')

    diff_comment = M.DiffComment(
        text=comment_text,
        line_start=line_start,
        filename=filename,
        user=request.user,
    )
    revision.diff_comments.append(diff_comment)

    return {
        'html': h.render_diff_comment(line_start, [diff_comment])
    }


@view_config(
    route_name='revision_policy',
    permission='comment',
)
def revision_policy(request):
    """Set the status of a RevisionPolicyCheck

    POST /revisions/:id/policy

    """
    revision = request.context
    policy_id = int(request.params.get('policy_id'))
    status = int(request.params.get('status', 0))

    policy_check = revision.get_policy_check_for(policy_id)
    if not policy_check:
        policy_check = M.RevisionPolicyCheck(
            revision_id=revision.id,
            policy_id=policy_id
        )
        M.DBSession().add(policy_check)
    policy_check.status = status

    return HTTPOk()
