
from remote.remote_config import DATABASE_URI as SQLALCHEMY_DATABASE_URI
from remote.remote_config import MIGRATE_REPO as SQLALCHEMY_MIGRATE_REPO

raise Exception('I don\'t think you should need to be doing this anymore'
                'Now we\'re using instances to automatically make and trackdatabases')
# def remote_db_create():
#     _remote_db.create_all_and_repo(SQLALCHEMY_MIGRATE_REPO, SQLALCHEMY_DATABASE_URI)
# LOL no way any of this works

