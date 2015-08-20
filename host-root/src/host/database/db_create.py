import os, sys
sys.path.append(os.path.join(os.path.join(sys.path[0], '..'), '..'))#dirtyhack
# REALLY FUCKING DIRTY
from host.host_config import DATABASE_URI as SQLALCHEMY_DATABASE_URI
from host.host_config import MIGRATE_REPO as SQLALCHEMY_MIGRATE_REPO
from host import host_db


host_db.create_all_and_repo(SQLALCHEMY_MIGRATE_REPO, SQLALCHEMY_DATABASE_URI)
# LOL no way any of this works

