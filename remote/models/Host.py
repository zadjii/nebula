import json
import socket
# from msg_codes import send_msg
from datetime import datetime
from common_util import datetime_to_string

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
            # TODO: Who's depending upon these?
            # , 'last_update': datetime_to_string(self.last_update)
            # , 'last_handshake': datetime_to_string(self.last_handshake)
        }
        return self_dict

    def to_json(self):
        # todo: Replace this with a proper marshmallow implementation
        return json.dumps(self.to_dict())

    def ip(self):
        return self.ipv6

    def handshake_now(self, ip, port, wsport, hostname):
        # TODO: The host should actually be the one tracking the "handshake"
        # time for all it's Mirror's. Mirros more care about the _sync_ time. So
        # we should move last_handshake up here.
        #
        # Until then, mark all our mirrors as having handshaked now.
        now = datetime.utcnow()
        for m in self.mirrors.all():
            m.last_handshake = now

        self.ipv6 = ip
        self.port = port
        self.ws_port = wsport
        self.hostname = hostname

        # TODO: We should probably also be updating the clouds size. We're no
        # longer doing that since we're not sending HostHandshakes anymore.
        # * Should we start sending those?
        # * Should we move that information into HostMoveRequest? MirrorHandshake?
        #   - I think I put those fields in MirrorHandshake without really
        #     thinking it through. Don't take that as gospel/intentional.

