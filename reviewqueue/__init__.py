from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.events import BeforeRender
from pyramid.request import Request
from pyramid.security import Allow
from pyramid.security import Everyone
from pyramid.security import unauthenticated_userid

from sqlalchemy import engine_from_config

from . import helpers
from . import models as M


def add_renderer_globals(event):
    event['h'] = helpers


def groupfinder(userid, request):
    user = request.user
    if user is not None:
        groups = ['{0}'.format(userid)]
        if user.is_charmer:
            groups.append('charmers')
        return groups
    return None


def validate_settings(settings):
    settings['base_url'] = (settings.get('base_url') or '').rstrip('/')
    return settings


class CustomRequest(Request):
    @reify
    def user(self):
        userid = unauthenticated_userid(self)
        if userid is not None:
            return M.User.get(userid)
        return None


class RootFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
    ]

    def __init__(self, request):
        self.request = request


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings = validate_settings(settings)

    engine = engine_from_config(settings, 'sqlalchemy.')
    M.DBSession.configure(bind=engine)
    M.Base.metadata.bind = engine

    authn_policy = AuthTktAuthenticationPolicy(
        settings['auth.secret'],
        callback=groupfinder,
        hashalg='sha512',
    )
    authz_policy = ACLAuthorizationPolicy()

    config = Configurator(
        settings=settings,
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
        request_factory=CustomRequest,
        root_factory=RootFactory,
    )
    config.add_subscriber(add_renderer_globals, BeforeRender)

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.include('reviewqueue.views.auth')
    config.include('reviewqueue.views.home')
    config.include('reviewqueue.views.reviews')
    config.include('reviewqueue.views.users')
    config.include('reviewqueue.views.revisions')
    config.include('reviewqueue.views.revision_tests')
    if settings.get('mail.host'):
        config.include('pyramid_mailer')

    config.scan()
    return config.make_wsgi_app()
