import logging

from pyramid.security import forget
from pyramid.security import remember
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from ..db import DB
from .. import models as M

log = logging.getLogger(__name__)


def includeme(config):
    config.include('velruse.providers.openid')
    config.add_openid_login()

    config.add_route('logout', '/logout')
    config.add_route('login', '/login')


@view_config(context='velruse.AuthenticationComplete')
def login_callback(request):
    """Ubuntu SSO calls back here after login attempt.

    """
    log.debug('openid callback request params: %s', request.params)
    mode = request.params.get('openid.mode')

    if mode != 'id_res':
        return HTTPFound(location=request.route_url('home'))

    user_data = dict(
        openid_claimed_id=request.params.get('openid.claimed_id'),
        nickname=request.params.get('openid.sreg.nickname'),
        fullname=request.params.get('openid.sreg.fullname'),
        email=request.params.get('openid.sreg.email'),
    )

    db = DB()
    user = M.User.get(openid_claimed_id=user_data['openid_claimed_id'])

    if user:
        user.update(**user_data)
    else:
        user = db.create_user(
            request.registry.settings,
            **user_data)
        db.flush()

    headers = remember(request, user.id)
    destination = request.session.get('redirect_to')
    if destination:
        del request.session['redirect_to']
    else:
        destination = request.route_url('home')

    return HTTPFound(location=destination, headers=headers)


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.route_url('home'), headers=headers)


@view_config(route_name='login')
def login(request):
    request.session['redirect_to'] = request.referer

    return HTTPFound(
        location='/login/openid?openid_identifier=http://login.ubuntu.com')
