from datetime import datetime

from pyramid.httpexceptions import HTTPOk
from pyramid.security import Allow
from pyramid.security import Everyone
from pyramid.view import view_config

from ..db import DB


def includeme(config):
    config.add_route(
        'revision_tests_callback', '/revision_tests/{id}',
        factory=RevisionTestFactory, traverse='/{id}')


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

    GET /revision_tests/:id

    """
    revision_test = request.context

    revision_test.status = request.params.get('status')
    revision_test.url = request.params.get('build_url')
    if revision_test.status != 'RUNNING':
        revision_test.finished = datetime.utcnow()

    return HTTPOk
