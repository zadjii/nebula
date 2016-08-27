from migrate.versioning import api
import os, sys
sys.path.append(os.path.join(os.path.join(sys.path[0], '..'), '..'))#dirtyhack fixme
# REALLY FUCKING DIRTY
from host.host_config import DATABASE_URI as SQLALCHEMY_DATABASE_URI
from host.host_config import MIGRATE_REPO as SQLALCHEMY_MIGRATE_REPO

api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print 'Current database version: ' + str(api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO))