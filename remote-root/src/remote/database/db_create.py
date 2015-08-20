import os, sys
sys.path.append(os.path.join(os.path.join(sys.path[0], '..'), '..'))  # dirtyhack
# REALLY FUCKING DIRTY
# fixme
from remote.remote_config import DATABASE_URI as SQLALCHEMY_DATABASE_URI
from remote.remote_config import MIGRATE_REPO as SQLALCHEMY_MIGRATE_REPO
from remote import remote_db


remote_db.create_all_and_repo(SQLALCHEMY_MIGRATE_REPO, SQLALCHEMY_DATABASE_URI)
# LOL no way any of this works

