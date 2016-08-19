import os
import ConfigParser

from datetime import timedelta

from celery import Celery


app_ini = '%s.ini' % os.environ.get('ENV', 'development')

config = ConfigParser.RawConfigParser()
config.read(app_ini)

admins = [(i, i) for i in eval(config.get('handler_exc', 'args'))[2]]

celery = Celery('reviewqueue.celery',
                broker=config.get('celery', 'broker'),
                backend=config.get('celery', 'backend'),
                include=['reviewqueue.tasks'])

# Optional configuration, see the application user guide.
celery.conf.update(
    CELERY_IGNORE_RESULT=True,
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
    CELERY_SEND_TASK_ERROR_EMAILS=True,
    ADMINS=admins,
    SERVER_EMAIL=config.get('app:main', 'mail.default_sender'),
    EMAIL_HOST=config.get('app:main', 'mail.host'),
    EMAIL_PORT=config.get('app:main', 'mail.port'),
)

if __name__ == '__main__':
    celery.start()
