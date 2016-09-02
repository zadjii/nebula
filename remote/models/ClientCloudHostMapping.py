from datetime import datetime, timedelta

from remote import _remote_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, BigInteger
from sqlalchemy.orm import relationship, backref

__author__ = 'Mike'


class ClientCloudHostMapping(db.Base):
    __tablename__ = 'clientcloudhostmapping'
    id = Column(Integer, primary_key=True)
    session_id = Column(ForeignKey('session.id'))
    cloud_id = Column(ForeignKey('cloud.id'))
    host_id = Column(ForeignKey('host.id'))

    def __init__(self, session, cloud, host):
        self.session_id = session.id
        self.cloud_id = cloud.id
        self.host_id = host.id


