def includeme(config):
    config.add_view(lambda x: {}, renderer='exc/500.mako', context=Exception)
