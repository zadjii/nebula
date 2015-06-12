__author__ = 'Mike'

from remote_config import DATABASE_URI
from database.SimpleDB import SimpleDB

remote_db = SimpleDB(DATABASE_URI)

from models.User import User


