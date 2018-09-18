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


class Host(base):
    __tablename__ = 'host'

    id = Column(Integer, primary_key=True)
    ipv6 = Column(String)
    port = Column(Integer)
    ws_port = Column(Integer)
    hostname = Column(String)
    last_certificate = Column(String)
    mirrors = relationship('Mirror', backref='host', lazy='dynamic')

    def send_msg(self, msg):
        raise Exception('If you find yourself doing this then that\'s the remote pushing to a host, which is NOT OKAY ')

    def to_dict(self):
        # todo: Replace this with a proper marshmallow implementation
        self_dict = {
            'curr_size': self.curr_size
            , 'ip': self.ipv6
            , 'port': self.port
            , 'ws_port': self.ws_port
            , 'hostname': self.hostname
            , 'remaining_size': self.remaining_size
            , 'last_update': (self.last_update.isoformat() + 'Z') if self.last_update else None
            , 'last_handshake': (self.last_handshake.isoformat() + 'Z') if self.last_handshake else None
        }
        return self_dict

    def to_json(self):
        # todo: Replace this with a proper marshmallow implementation
        return json.dumps(self.to_dict())

    def ip(self):
        return self.ipv6
