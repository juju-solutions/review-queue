# Review Queue


## Getting started

First install the app and it's deps:

    $ make .venv

### Postgres

You need access to a postgres server. Update the `sqlalchemy.url` option in
`development.ini` to point to your postgres server, with the correct
login credentials. You do not need to create the `reviewqueue` database.

### Redis

The review queue uses Celery for running background tasks, with redis as the data store. You need access to a redis server. Update the redis urls under the `celery` section of `development.ini` to point to your redis server. If you installed redis locally and haven't changed the port, the default config values will work -- you don't need to change anything.

### Launchpad Authentication

The Launchpad api is used to check users' group membership:

    $ .venv/bin/initialize_lp_creds

This will open up LaunchPad in your browser, requesting OAUTH access from the Review Queue application. The credentials will be cached in ```lp-creds```

**NOTE**: This will run all Launchpad api requests as your user.

### Run Celery worker

Run from the root project directory:

    $ celery -A reviewqueue.celerycfg worker -l info -B

Celery background tasks periodically refresh review info, updating test
results, ingesting new source revisions, etc.

### Run webserver

    $ make serve

Browse to the app at http://localhost:6542
