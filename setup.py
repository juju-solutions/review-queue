import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'arrow',
    'binaryornot',
    'cached_property',
    'celery[redis]',
    'jsonschema',
    'launchpadlib',
    'psycopg2',
    'pygments',
    'pyramid',
    'pyramid_mako',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'pyyaml',
    'requests==2.6.0',
    'simplejson',
    'sqlalchemy',
    'sqlalchemy-utils',
    'theblues',
    'transaction',
    'zope.sqlalchemy',
    'velruse',
    'waitress',
    ]

setup(
    name='review-queue',
    version='0.0',
    description='review-queue',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='',
    author_email='',
    url='',
    keywords='web wsgi bfg pylons pyramid',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='reviewqueue',
    install_requires=requires,
    entry_points="""\
    [paste.app_factory]
    main = reviewqueue:main
    [console_scripts]
    initialize_db = reviewqueue.scripts.initializedb:main
    initialize_lp_creds = reviewqueue.helpers:get_lp
    """,
)
