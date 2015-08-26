from remote import _remote_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref

__author__ = 'Mike'


class Host(db.Base):
    __tablename__ = 'host'

    id = Column(Integer, primary_key=True)
    cloud_id = Column(ForeignKey('cloud.id'))
    last_update = Column(DateTime)
    last_handshake = Column(DateTime)
    curr_size = Column(Integer)  # Cloud size in bytes
    remaining_size = Column(Integer)  # remaining free space on host (in bytes)
    ip = Column(String)
    port = Column(Integer)
