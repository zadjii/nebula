import json
import socket
# from msg_codes import send_msg
from datetime import datetime

from connections.RawConnection import RawConnection
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table,\
    Boolean
from sqlalchemy.orm import relationship, backref
from remote.models import nebr_base as base

__author__ = 'Mike'


class Mirror(base):
    __tablename__ = 'mirror'

    id = Column(Integer, primary_key=True)
    cloud_id = Column(ForeignKey('cloud.id'))
    host_id = Column(ForeignKey('host.id'))
    last_update = Column(DateTime)
    last_handshake = Column(DateTime)
    curr_size = Column(Integer)  # Cloud size in bytes
    remaining_size = Column(Integer)  # remaining free space on host (in bytes)

    client_mappings = relationship('ClientCloudHostMapping', backref='mirror', lazy='dynamic')
    completed_mirroring = Column(Boolean)

    def is_active(self):
        if not self.completed_mirroring:
            return False
        if self.last_handshake is None:
            return False
        delta = datetime.utcnow() - self.last_handshake
        if delta.seconds / 60 <= 1:
            return True
        return False

    def send_msg(self, msg):
        raise Exception('If you find yourself doing this then that\'s the remote pushing to a host, which is NOT OKAY ')

    def to_dict(self):
        # todo: Replace this with a proper marshmallow implementation

        self_dict = {
            'curr_size': self.curr_size
            , 'ip': self.host.ipv6
            , 'port': self.host.port
            , 'ws_port': self.host.ws_port
            , 'hostname': self.host.hostname
            , 'remaining_size': self.remaining_size
            , 'last_update': (self.last_update.isoformat() + 'Z') if self.last_update else None
            , 'last_handshake': (self.last_handshake.isoformat() + 'Z') if self.last_handshake else None
        }
        return self_dict

    def to_json(self):
        # todo: Replace this with a proper marshmallow implementation
        return json.dumps(self.to_dict())

