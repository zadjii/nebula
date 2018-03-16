import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref

from common_util import INFINITE_SIZE
from remote.models import nebr_base as base
from remote.models.Host import Host
from remote.models.Mirror import Mirror

__author__ = 'Mike'


cloud_owners = Table(
    'cloud_owners'
    , base.metadata
    , Column('cloud_id', Integer, ForeignKey('cloud.id'))
    , Column('user_id', Integer, ForeignKey('user.id'))
    )
cloud_contributors = Table(
    'cloud_contributors'
    , base.metadata
    , Column('cloud_id', Integer, ForeignKey('cloud.id'))
    , Column('user_id', Integer, ForeignKey('user.id'))
    )

# These definitions left here as we change the meanings.
# HIDDEN_CLOUD = 0  # only owners can access IP
# PRIVATE_CLOUD = 1  # only owners and contributors
# PUBLIC_CLOUD = 2  # anyone (host can still reject RDWR)
# # todo: when making links, host needs to know privacy state. If a host wants to
# # cont make a public link, then the cloud needs to be public, etc.

PRIVATE_CLOUD = 1 # No file on the coud was ever shared with the public.
PUBLIC_CLOUD = 2 # At least one file was shared with the public.
# Honestly, we could still probably just do away with this...
# We'd make all clouds public, and then it'd be the host's responsibility to reject the requests.
# Kinda shitty though, to have all hosts ddos-able...

class Cloud(base):
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
    # hosts = relationship('Host', backref='cloud', lazy='dynamic')
    mirrors = relationship('Mirror', backref='cloud', lazy='dynamic')
    last_update = Column(DateTime)
    max_size = Column(Integer, default=INFINITE_SIZE)  # Cloud size in bytes
    # If this is set to public, then at least one file was shared publicly.
    privacy = Column(Integer, default=PRIVATE_CLOUD)

    creator_id = Column(ForeignKey('user.id'))
    # sessions = relationship('Session', backref='cloud', lazy='dynamic')

    def __init__(self, creator):
        self.creator_id = creator.id
        self.owners.append(creator)
        self.created_on = datetime.utcnow()
        self.last_update = datetime.utcnow()
        self.privacy = PRIVATE_CLOUD
        self.max_size = -1

    def is_hidden(self):
        # return self.privacy == HIDDEN_CLOUD
        # The cloud has been shared with no one.
        return self.contributors.count() == 0 and self.privacy == PRIVATE_CLOUD

    def is_private(self):
        # The cloud has been shared, but no file is publicly available.
        return self.privacy == PRIVATE_CLOUD

    def is_public(self):
        # There is at least one file that has been shared with the public.
        return self.privacy == PUBLIC_CLOUD

    def has_owner(self, user):
        return self.owners.filter_by(id=user.id).first() is not None

    def has_contributor(self, user):
        return self.contributors.filter_by(id=user.id).first() is not None

    def add_owner(self, user):
        if not self.has_owner(user):
            self.owners.append(user)

    def add_contributor(self, user):
        if not self.has_contributor(user):
            self.contributors.append(user)

    def can_access(self, user):
        if self.is_public():
            return True
        elif self.is_private():
            return self.has_owner(user) or self.has_contributor(user)
        else: # self.is_hidden():
            return self.has_owner(user)

    def active_hosts(self):
        mirrors = []
        for mirror in self.mirrors.all():
            if mirror.is_active():
                mirrors.append(mirror)
        return mirrors

    def creator_name(self):
        # todo/fixme: this is temporary until I add uname properly to the DB
        # first_owner = self.owners.first()
        # if first_owner is not None:
        #     return first_owner.username
        # return None
        return self.uname()

    def uname(self):
        # type: () -> str
        return self.creator.get_username()

    def cname(self):
        # type: () -> str
        return self.name

    def full_name(self):
        # type: () -> str
        return '{}/{}'.format(self.uname(), self.name)

    def available_space(self):
        """
        Returns the minimum of the space available on this cloud.
        :return:
        """
        min_host = self.mirrors.order_by(Mirror.remaining_size).first()
        min = min_host.remaining_size if min_host is not None else self.max_size
        return min

    def to_dict(self):
        self_dict = {
            'uname': self.uname()
            , 'cname': self.cname()
            , 'created_on': self.created_on.isoformat() + 'Z"'
            , 'last_update': self.last_update.isoformat() + 'Z"'
            , 'max_size': self.max_size
            , 'available_space': self.available_space()
            , 'privacy': self.privacy
        }
        return self_dict

    def to_json(self):
        # todo: Replace this with a proper marshmallow implementation
        return json.dumps(self.to_dict())

    def make_public(self):
        self.privacy = PUBLIC_CLOUD

    def get_get_hosts_dict(self, active_only=False):
        # type: (bool) -> [dict]
        """
        The GetHostsResponse and the GetActiveHostsResponse messages have this
          weird array of dicts that they respond with, containing info for
          each of the mirrors. This gets the relevant data for those messages.
        :param active_only:
        :return:
        """
        mirror_dicts = []
        for mirror in self.mirrors:
            if active_only and not mirror.is_active():
                continue
            mirror_obj = {
                'ip': mirror.host.ip()
                , 'port': mirror.host.port
                , 'wsport': mirror.host.ws_port
                , 'id': mirror.id
                , 'update': mirror.last_update
                , 'hndshk': mirror.last_handshake.isoformat()
                , 'hostname': mirror.host.hostname
            }
            mirror_dicts.append(mirror_obj)
        return mirror_dicts
