# last generated 2020-03-06 02:25:52.550000
from messages import BaseMessage
from msg_codes import MIRROR_HANDSHAKE as MIRROR_HANDSHAKE
__author__ = 'Mike'


class MirrorHandshakeMessage(BaseMessage):
    def __init__(self, mirror_id=None, last_sync=None, last_modified=None, hostname=None, used_space=None, remaining_space=None):
        super(MirrorHandshakeMessage, self).__init__()
        self.type = MIRROR_HANDSHAKE
        self.mirror_id = mirror_id
        self.last_sync = last_sync
        self.last_modified = last_modified
        self.hostname = hostname
        self.used_space = used_space
        self.remaining_space = remaining_space

    @staticmethod
    def deserialize(json_dict):
        msg = MirrorHandshakeMessage()
        msg.mirror_id = json_dict['mirror_id']
        msg.last_sync = json_dict['last_sync']
        msg.last_modified = json_dict['last_modified']
        msg.hostname = json_dict['hostname']
        msg.used_space = json_dict['used_space']
        msg.remaining_space = json_dict['remaining_space']
        return msg

