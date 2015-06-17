from remote import remote_db

__author__ = 'Mike'

from sqlalchemy import Column, Integer, String, DateTime
# from .. import remote_db


class User(remote_db.Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    name = Column(String)
    password = Column(String)
    created_on = Column(DateTime)