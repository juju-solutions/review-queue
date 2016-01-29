import argparse
import logging
import transaction

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

import sqlalchemy
from sqlalchemy import engine_from_config
from sqlalchemy_utils import (
    create_database,
    database_exists,
)

from reviewqueue import models as M


log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ini_file')
    parser.add_argument(
        '-f', '--force', action='store_true',
        help='If tables exist, drop and recreate'
    )
    args = parser.parse_args()

    setup_logging(args.ini_file)
    settings = get_appsettings(args.ini_file)
    engine = engine_from_config(settings, 'sqlalchemy.')

    try:
        if not database_exists(engine.url):
            create_database(engine.url)
    except sqlalchemy.exc.OperationalError as e:
        log.warn("Couldn't create database: %s", e)

    M.DBSession.configure(bind=engine)
    if args.force:
        M.Base.metadata.drop_all(engine)
    M.Base.metadata.create_all(engine)

    if args.force:
        # Insert some stuff
        with transaction.manager:
            M.DBSession.add_all([
                M.Policy(description="Must have passing tests"),
                M.Policy(description="Must have hooks that are idempotent"),
                M.Policy(description="Must not have immutable configuration"),
            ])
