import os
import ConfigParser

from datetime import timedelta

from celery import Celery


app_ini = '%s.ini' % os.environ.get('ENV', 'development')

config = ConfigParser.RawConfigParser()
config.read(app_ini)

celery = Celery('reviewqueue.celery',
                broker=config.get('celery', 'broker'),
                backend=config.get('celery', 'backend'),
                include=['reviewqueue.tasks'])

# Optional configuration, see the application user guide.
celery.conf.update(
    CELERY_BACKEND_TRANSPORT_OPTIONS=config.get(
        'celery', 'backend_transport_options'),
    CELERY_ACCEPT_CONTENT=['pickle'],
    CELERY_TIMEZONE='UTC',
    CELERYBEAT_SCHEDULE={
        'refresh_reviews': {
            'task': 'reviewqueue.tasks.refresh_reviews',
            'schedule': timedelta(seconds=60),
        },
    },
)

if __name__ == '__main__':
    celery.start()
