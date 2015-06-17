__author__ = 'Mike'

from remote_config import DATABASE_URI
from database.SimpleDB import SimpleDB

remote_db = SimpleDB(DATABASE_URI)
remote_db.engine.echo = False

from models.User import User
User.query = remote_db.session.query(User)  # todo: find a way to do this automatically.


