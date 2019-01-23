# last generated 2018-11-06 16:18:02.831000
from messages import BaseMessage
from msg_codes import HOST_HANDSHAKE as HOST_HANDSHAKE
__author__ = 'Mike'


class HostHandshakeMessage(BaseMessage):
    def __init__(self, id=None, ipv6=None, port=None, wsport=None, last_sync=None, last_modified=None, hostname=None, used_space=None, remaining_space=None):
        super(HostHandshakeMessage, self).__init__()
        self.type = HOST_HANDSHAKE
        self.id = id
        self.ipv6 = ipv6
        self.port = port
        self.wsport = wsport
        self.last_sync = last_sync
        self.last_modified = last_modified
        self.hostname = hostname
        self.used_space = used_space
        self.remaining_space = remaining_space

    @staticmethod
    def deserialize(json_dict):
        msg = HostHandshakeMessage()
        msg.id = json_dict['id']
        msg.ipv6 = json_dict['ipv6']
        msg.port = json_dict['port']
        msg.wsport = json_dict['wsport']
        msg.last_sync = json_dict['last_sync']
        msg.last_modified = json_dict['last_modified']
        msg.hostname = json_dict['hostname']
        msg.used_space = json_dict['used_space']
        msg.remaining_space = json_dict['remaining_space']
        return msg

