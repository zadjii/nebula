from werkzeug.security import check_password_hash
from sqlalchemy import Column, Integer, String, DateTime
# from .. import remote_db
from sqlalchemy.orm import relationship, backref
from remote.models import nebr_base as base
__author__ = 'Mike'

class User(base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    name = Column(String)
    password = Column(String)
    created_on = Column(DateTime)

    sessions = relationship('Session', backref='user', lazy='dynamic')

    created_clouds = relationship('Cloud', backref='creator', lazy='dynamic')

    def check_password(self, provided_password):
        return check_password_hash(self.password, provided_password)

    def get_username(self):
        return self.username.lower()
