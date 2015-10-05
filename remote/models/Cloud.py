from remote import _remote_db as db
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


HIDDEN_CLOUD = 0  # only owners can access IP
PRIVATE_CLOUD = 1  # only owners and contributors
PUBLIC_CLOUD = 2  # anyone (host can still reject RDWR)
# todo: when making links, host needs to know privacy state. If a host wants to
# cont make a public link, then the cloud needs to be public, etc.

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
    privacy = Column(Integer, default=PRIVATE_CLOUD)

    sessions = relationship('Session', backref='cloud', lazy='dynamic')

    def is_hidden(self):
        return self.privacy == HIDDEN_CLOUD

    def is_private(self):
        return self.privacy == PRIVATE_CLOUD

    def is_public(self):
        return self.privacy == PUBLIC_CLOUD

    def can_access(self, user):
        if self.is_hidden():
            return self.owners.filter_by(id=user.id).first() is not None
        elif self.is_private():
            return self.owners.filter_by(id=user.id).first() is not None \
                or self.contributors.filter_by(id=user.id).first() is not None
        else:
            return True
