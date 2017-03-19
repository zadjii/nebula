__author__ = 'Mike'

# from remote_config import DATABASE_URI, MIGRATE_REPO
# from database.SimpleDB import SimpleDB
#
# _remote_db = SimpleDB(DATABASE_URI)
# _remote_db.engine.echo = False
# note: He unfortunately needs to stay around,
#  so we can set up ORM metadata.

from models.User import User
from models.Cloud import Cloud
from models.Host import Host
from models.Session import Session
from models.ClientCloudHostMapping import ClientCloudHostMapping
from models.HostHostFetchMapping import HostHostFetchMapping
# User.query = remote_db.session.query(User)
# Cloud.query = remote_db.session.query(Cloud)
# Host.query = remote_db.session.query(Host)
# todo: find a way to do this ^^^ automatically.


# todo: find out if the DB migrate repo was already created.
# todo: if it wasn't, then make both of them.
# remote_db.create_all_and_repo(MIGRATE_REPO, DATABASE_URI)

