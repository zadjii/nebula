import json
import socket
# from msg_codes import send_msg
from datetime import datetime

from connections.RawConnection import RawConnection
from host import HOST_PORT
from remote import _remote_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table,\
    Boolean
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
    ipv4 = Column(String)
    ipv6 = Column(String)
    port = Column(Integer)
    ws_port = Column(Integer)
    hostname = Column(String)
    # sessions = relationship('Session', backref='host', lazy='dynamic')
    client_mappings = relationship('ClientCloudHostMapping', backref='host', lazy='dynamic')

    # note: leaving this here. The host will only be in the list of hosts
    # cont    for a cloud if it's sent a completed_mirroring.
    # completed_mirroring = Column(Boolean, default=False)

    def is_active(self):
        if self.last_handshake is None:
            return False
        delta = datetime.utcnow() - self.last_handshake
        if delta.seconds / 60 <= 1:
            return True
        return False

    def send_msg(self, msg):
        # print 'rand host is ({},{})'.format(ip, port)
        # context = SSL.Context(SSL.SSLv23_METHOD)
        # context.use_privatekey_file(KEY_FILE)
        # context.use_certificate_file(CERT_FILE)
        # todo SSL
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # s = SSL.Connection(context, s)
        # whatever fuck it lets just assume it's good todo
        s.connect((self.ipv6, self.port, 0, 0))
        conn = RawConnection(s)
        conn.send_obj(msg)
        # send_msg(msg, s)
        s.close()
        # todo I think maybe part of the close after close is related to this...

    def to_dict(self):
        # todo: Replace this with a proper marshmallow implementation
        self_dict = {
            'curr_size': self.curr_size
            , 'ip': self.ipv6
            , 'port': self.port
            , 'wsport': self.wsport
            , 'hostname': self.hostname
            , 'remaining_size': self.remaining_size
        }
        return self_dict

    def to_json(self):
        # todo: Replace this with a proper marshmallow implementation
        return json.dumps(self.to_dict())

