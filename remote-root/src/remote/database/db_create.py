from migrate.versioning import api
import os

from remote.remote_config import DATABASE_URI as SQLALCHEMY_DATABASE_URI
from remote.remote_config import MIGRATE_REPO as SQLALCHEMY_MIGRATE_REPO
from remote import remote_db


remote_db.create_all()  # LOL no way any of this works

print 'The database should have been created here'

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))

print 'The migration repo should have been created here'
