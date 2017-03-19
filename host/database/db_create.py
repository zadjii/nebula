from host.host_config import DATABASE_URI as SQLALCHEMY_DATABASE_URI
from host.host_config import MIGRATE_REPO as SQLALCHEMY_MIGRATE_REPO
raise Exception('I don\'t think you should need to be doing this anymore'
                'Now we\'re using instances to automatically make and trackdatabases')
# from host import _host_db
#
# def host_db_create():
#     _host_db.create_all_and_repo(SQLALCHEMY_MIGRATE_REPO, SQLALCHEMY_DATABASE_URI)
# LOL no way any of this works

