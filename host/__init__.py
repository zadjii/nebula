__author__ = 'zadjii'

from host_config import DATABASE_URI, MIGRATE_REPO
from database.SimpleDB import SimpleDB

_host_db = SimpleDB(DATABASE_URI)
_host_db.engine.echo = False

from models.Cloud import Cloud
from models.FileNode import FileNode
from models.IncomingHostEntry import IncomingHostEntry
from models.Session import Session

# Cloud.query = host_db.session.query(Cloud)
# FileNode.query = host_db.session.query(FileNode)
# IncomingHostEntry.query = host_db.session.query(IncomingHostEntry)
# todo: find a way to do this ^^^ automatically.


# todo: find out if the DB migrate repo was already created.
# todo: if it wasn't, then make both of them.
# remote_db.create_all_and_repo(MIGRATE_REPO, DATABASE_URI)

def get_db():
    db = SimpleDB(DATABASE_URI)
    db.engine.echo = False
    return db


REMOTE_HOST = 'localhost'
REMOTE_PORT = 12345
HOST_HOST = ''
HOST_PORT = 23456

