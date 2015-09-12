from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


def includeme(config):
    config.add_route('home', '/')


@view_config(route_name='home', renderer='index.mako')
def home(request):
    """Home page

    GET /

    """
    return HTTPFound(
        location=request.route_url('reviews_index'))
