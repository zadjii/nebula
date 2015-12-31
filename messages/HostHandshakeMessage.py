# last generated 2015-12-31 02:30:42.288000
from messages import BaseMessage
from msg_codes import HOST_HANDSHAKE as HOST_HANDSHAKE
__author__ = 'Mike'


class HostHandshakeMessage(BaseMessage):
    def __init__(self, id=None, port=None, wsport=None, update=None):
        super(HostHandshakeMessage, self).__init__()
        self.type = HOST_HANDSHAKE
        self.id = id
        self.port = port
        self.wsport = wsport
        self.update = update

    @staticmethod
    def deserialize(json_dict):
        msg = HostHandshakeMessage()
        msg.id = json_dict['id']
        msg.port = json_dict['port']
        msg.wsport = json_dict['wsport']
        msg.update = json_dict['update']
        return msg

