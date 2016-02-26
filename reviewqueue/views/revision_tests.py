from datetime import datetime

from pyramid.httpexceptions import HTTPOk
from pyramid.security import Allow
from pyramid.security import Everyone
from pyramid.view import view_config

from ..db import DB
from .. import tasks


def includeme(config):
    config.add_route(
        'revision_tests_callback', '/revision_tests/{id}',
        factory=RevisionTestFactory, traverse='/{id}',
        request_method='POST')
    config.add_route(
        'revision_tests_show', '/revision_tests/{id}',
        factory=RevisionTestFactory, traverse='/{id}',
        request_method='GET')


class RevisionTestFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        revision_test = DB().get_revision_test(id=key)
        if not revision_test:
            raise KeyError(
                "No revision test with id '%s'" % key)

        revision_test.__parent__ = self
        revision_test.__name__ = key
        return revision_test


@view_config(
    route_name='revision_tests_callback',
    renderer='json',
    permission='view',
)
def revision_tests_callback(request):
    """Test completion callback.

    Jenkins posts test results to this url

    POST /revision_tests/:id

    """
    revision_test = request.context

    revision_test.status = request.params.get('status')
    revision_test.url = request.params.get('build_url')
    if revision_test.status != 'RUNNING':
        revision_test.finished = datetime.utcnow()
        tasks.refresh_review.delay(revision_test.revision.review)

    return HTTPOk()


@view_config(
    route_name='revision_tests_show',
    renderer='revision_tests/show.mako',
    permission='view',
)
def revision_tests_show(request):
    """Show results of a single RevisionTest.

    Renders html results parsed from the json file
    downloaded from Jenkins and stored on the RevisionTest.

    GET /revision_tests/:id

    """
    revision_test = request.context

    return {
        'revision_test': revision_test,
    }
