from datetime import datetime, timedelta
from uuid import uuid4

from remote import _remote_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, BigInteger
from sqlalchemy.orm import relationship, backref
from remote.models.ClientCloudHostMapping import ClientCloudHostMapping
__author__ = 'Mike'


class Session(db.Base):
    __tablename__ = 'session'

    id = Column(Integer, primary_key=True)
    # cloud_id = Column(ForeignKey('cloud.id'))
    user_id = Column(ForeignKey('user.id'))
    host_id = Column(ForeignKey('host.id'))
    uuid = Column(String)  # todo:11 length should be the uuid length
    # todo:11 fix the type of this ^
    created_on = Column(DateTime)
    last_refresh = Column(DateTime)

    host_mappings = relationship('ClientCloudHostMapping'
                                 , backref='session'
                                 , lazy='dynamic')


    def __init__(self, user):
        now = datetime.utcnow()
        self.created_on = now
        self.last_refresh = now
        self.user = user
        sess_uuid = str(uuid4())
        self.uuid = sess_uuid
        # todo:11 this is probably bad. Maybe store the numeric value or something.

    def has_timed_out(self):
        delta = datetime.utcnow() - self.last_refresh
        return (delta.seconds/60) > 30
