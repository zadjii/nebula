from remote import remote_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref


__author__ = 'Mike'


cloud_owners = Table(
    'cloud_owners'
    , db.Base.metadata
    , Column('cloud_id', Integer, ForeignKey('cloud.id'))
    , Column('user_id', Integer, ForeignKey('user.id'))
    )
cloud_contributors = Table(
    'cloud_contributors'
    , db.Base.metadata
    , Column('cloud_id', Integer, ForeignKey('cloud.id'))
    , Column('user_id', Integer, ForeignKey('user.id'))
    )


class Cloud(db.Base):
    __tablename__ = 'cloud'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_on = Column(DateTime)
    owners = relationship(
        "User"
        , secondary=cloud_owners
        , backref=backref('owned_clouds', lazy='dynamic')
        , lazy='dynamic'
        )
    contributors = relationship(
        "User"
        , secondary=cloud_contributors
        , backref=backref('contributed_clouds', lazy='dynamic')
        , lazy='dynamic'
        )
    hosts = relationship('Host', backref='cloud', lazy='dynamic')
    last_update = Column(DateTime)
    max_size = Column(Integer)  # Cloud size in bytes
