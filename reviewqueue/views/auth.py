import logging

from pyramid.security import forget
from pyramid.security import remember
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from ..db import DB

log = logging.getLogger(__name__)


def includeme(config):
    config.include('velruse.providers.openid')
    config.add_openid_login()

    config.add_route('logout', '/logout')


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
    user = db.get_user(openid_claimed_id=user_data['openid_claimed_id'])

    if user:
        user.update(**user_data)
    else:
        user = db.create_user(**user_data)
        db.flush()

    headers = remember(request, user.id)
    return HTTPFound(
        location=request.route_url('home'),
        headers=headers)


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(
        location=request.route_url('home'),
        headers=headers)
