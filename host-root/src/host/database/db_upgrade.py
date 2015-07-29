from migrate.versioning import api

from remote.remote_config import DATABASE_URI as SQLALCHEMY_DATABASE_URI
from remote.remote_config import MIGRATE_REPO as SQLALCHEMY_MIGRATE_REPO

api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print 'Current database version: ' + str(api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO))