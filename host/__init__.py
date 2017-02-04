from host import models

__author__ = 'zadjii'

from host_config import DATABASE_URI, MIGRATE_REPO
from database.SimpleDB import SimpleDB

# fixme I believe I should remove the DATABASE_URI here.
#   We'll still use this instance to import all the models, etc, but then we
#   can just use instance.get_db() to replace get_db()
#   and if the models are the same, it should be fine?
#
# It might also be better to just remove the reference to this SimpleDB all together.
#   The models all get imported with declarative_base()
#   NOTE: no
#   I think they all need to be declared on the same base instance.
#
# _host_db = SimpleDB(DATABASE_URI, models.nebs_base)
# _host_db.engine.echo = False

from models.Cloud import Cloud
from models.FileNode import FileNode
from models.IncomingHostEntry import IncomingHostEntry
from models.Client import Client

# Cloud.query = host_db.session.query(Cloud)
# FileNode.query = host_db.session.query(FileNode)
# IncomingHostEntry.query = host_db.session.query(IncomingHostEntry)
# todo: find a way to do this ^^^ automatically.


# todo: find out if the DB migrate repo was already created.
# todo: if it wasn't, then make both of them.
# remote_db.create_all_and_repo(MIGRATE_REPO, DATABASE_URI)


# # note:
# # See this is why I think I can get away with using a SimpleDB that does nothing above.
# # It's never used for anything other than instantiating all the imports.
# # ever other instance uses an instance made here
# def get_db():
#     db = SimpleDB(DATABASE_URI, models.nebs_base)
#     db.engine.echo = False
#     return db


REMOTE_HOST = 'localhost'
REMOTE_PORT = 12345
# HOST_HOST = ''
# HOST_PORT = 23456
# HOST_WS_HOST = '127.0.0.1'
# HOST_WS_PORT = 34567

