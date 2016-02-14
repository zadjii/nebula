from host import _host_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, BigInteger
from sqlalchemy.orm import relationship, backref

__author__ = 'Mike'


class Session(db.Base):
    __tablename__ = 'session'

    id = Column(Integer, primary_key=True)

    # todo this needs to be a many-many, sessions have lots of clouds, clouds
    # cont have lots of sessions.
    cloud_id = Column(ForeignKey('cloud.id'))
    user_id = Column(Integer)
    # host_id = Column(ForeignKey('host.id'))
    uuid = Column(String)  # todo length should be the uuid length
    # todo right now we store an uint64(?) as a String, b/c no native sqlite sup
    created_on = Column(DateTime)
    last_refresh = Column(DateTime)
    client_ip = Column(String)
    # fixme what, we just ASSUME they're at HOST_PORT? that's dumb.
    # note: no you stupid itiot, we don't need to give them a port,
    # cont    they'll be connecting from random ports all the time


