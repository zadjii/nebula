import os
import platform
from datetime import datetime

from common_util import ResultAndData, mylog, get_free_space_bytes, INFINITE_SIZE
from connections.RawConnection import RawConnection
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, backref
from FileNode import FileNode
from host.models import nebs_base as base
from host.util import setup_ssl_socket_for_address
from messages import HostHandshakeMessage

__author__ = 'Mike'


class Remote(base):
    __tablename__ = 'remote'
    id = Column(Integer, primary_key=True)
    my_id_from_remote = Column(Integer)
    remote_address = Column(String)
    remote_port = Column(Integer)
    key = Column(String)
    certificate = Column(String)
    # crt_address is the address that we registered our cert with.
    crt_address = Column(String)
    last_cert_timestamp = Column(DateTime)

    #  probably todo: should make the remote handshakes independent
    # last_handshake = Column(DateTime)

    clouds = relationship('Cloud', backref='remote', lazy='dynamic')

    def __init__(self):
        pass

    def add_cloud(self, cloud):
        self.clouds.append(cloud)

    def set_certificate(self, address, cert):
        self.crt_address = address
        self.certificate = cert
        self.last_cert_timestamp = datetime.utcnow()

    def setup_socket(self):
        return setup_ssl_socket_for_address(self.remote_address, self.remote_port)

    def debug_str(self):
        return '[{}]: my_id={}, addr=[{}]:{}, crt=\n{}'.format(self.id, self.my_id_from_remote, self.remote_address, self.remote_port, self.certificate)
