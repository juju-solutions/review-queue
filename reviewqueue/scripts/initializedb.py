import argparse
import logging
import os
import transaction

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

import sqlalchemy
from sqlalchemy import engine_from_config
from sqlalchemy_utils import (
    create_database,
    drop_database,
    database_exists,
)
import yaml

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
        drop_database(engine.url)
        create_database(engine.url)
    M.Base.metadata.create_all(engine)

    if args.force:
        # Insert some stuff
        with transaction.manager:
            here = os.path.dirname(__file__)
            db_file = os.path.join(here, 'db.yaml')
            with open(db_file) as f:
                db = yaml.safe_load(f)

                for cat in db['categories']:
                    c = M.PolicyCategory(name=cat['name'])
                    for p in cat['policies']:
                        c.policies.append(
                            M.Policy(
                                description=p['description'],
                                tip=p['tip'],
                                required=p['required']))
                    M.DBSession.add(c)
