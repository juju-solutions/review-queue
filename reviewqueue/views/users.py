from pyramid.security import Allow
from pyramid.security import Everyone
from pyramid.view import view_config

from ..db import DB


def includeme(config):
    config.add_route(
        'users_show', '/users/{nickname}',
        factory=UserFactory, traverse='/{nickname}')


class UserFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        user = DB().get_user(nickname=key)
        if not user:
            raise KeyError(
                "No user with nickname '%s'" % key)

        user.__parent__ = self
        user.__name__ = key
        return user


@view_config(
    route_name='users_show',
    renderer='users/show.mako',
    permission='view',
)
def show(request):
    """Show a user profile page

    GET /users/:nickname

    """
    user = request.context

    return {
        'user': user,
    }
