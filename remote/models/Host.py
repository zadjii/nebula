import socket
from msg_codes import send_msg
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
    ip = Column(String)
    port = Column(Integer)
    sessions = relationship('Session', backref='host', lazy='dynamic')

    # note: leaving this here. The host will only be in the list of hosts
    # cont    for a cloud if it's sent a completed_mirroring.
    # completed_mirroring = Column(Boolean, default=False)

    def send_msg(self, msg):
        # print 'rand host is ({},{})'.format(ip, port)
        # context = SSL.Context(SSL.SSLv23_METHOD)
        # context.use_privatekey_file(KEY_FILE)
        # context.use_certificate_file(CERT_FILE)
        # todo SSL
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s = SSL.Connection(context, s)
        # whatever fuck it lets just assume it's good todo
        s.connect((self.ip, self.port))
        send_msg(msg, s)
        s.close()
