# last generated 2016-04-10 21:56:22.452000
from messages import BaseMessage
from msg_codes import HOST_HANDSHAKE as HOST_HANDSHAKE
__author__ = 'Mike'


class HostHandshakeMessage(BaseMessage):
    def __init__(self, id=None, ipv6=None, port=None, wsport=None, update=None, hostname=None):
        super(HostHandshakeMessage, self).__init__()
        self.type = HOST_HANDSHAKE
        self.id = id
        self.ipv6 = ipv6
        self.port = port
        self.wsport = wsport
        self.update = update
        self.hostname = hostname

    @staticmethod
    def deserialize(json_dict):
        msg = HostHandshakeMessage()
        msg.id = json_dict['id']
        msg.ipv6 = json_dict['ipv6']
        msg.port = json_dict['port']
        msg.wsport = json_dict['wsport']
        msg.update = json_dict['update']
        msg.hostname = json_dict['hostname']
        return msg

