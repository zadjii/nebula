import json
from messages import BaseMessage
from msg_codes import REMOTE_HANDSHAKE as REMOTE_HANDSHAKE
__author__ = 'Mike'


class RemoteHandshakeMessage(BaseMessage):
    def __init__(self, id=None, key=None, cert=None):
        super(RemoteHandshakeMessage, self).__init__()
        self.type = REMOTE_HANDSHAKE
        self.id = id
        self.key = key
        self.cert = cert

    @staticmethod
    def deserialize(json_dict):
        msg = RemoteHandshakeMessage()
        # msg.type = json_dict['type']
        # ^ I think it's assumed
        msg.id = json_dict['id']
        msg.key = json_dict['key']
        msg.cert = json_dict['cert']
        return msg

