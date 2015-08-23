__author__ = 'zadjii'

from host_config import DATABASE_URI, MIGRATE_REPO
from database.SimpleDB import SimpleDB

host_db = SimpleDB(DATABASE_URI)
host_db.engine.echo = False

from models.Cloud import Cloud
from models.FileNode import FileNode
from models.IncomingHostEntry import IncomingHostEntry

Cloud.query = host_db.session.query(Cloud)
FileNode.query = host_db.session.query(FileNode)
IncomingHostEntry.query = host_db.session.query(IncomingHostEntry)
# todo: find a way to do this ^^^ automatically.


# todo: find out if the DB migrate repo was already created.
# todo: if it wasn't, then make both of them.
# remote_db.create_all_and_repo(MIGRATE_REPO, DATABASE_URI)
