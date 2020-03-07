# last generated 2020-03-07 05:19:37.539000
from messages import BaseMessage
from msg_codes import REMOTE_MIRROR_HANDSHAKE as REMOTE_MIRROR_HANDSHAKE
__author__ = 'Mike'


class RemoteMirrorHandshakeMessage(BaseMessage):
    def __init__(self, id=None, new_sync=None, sync_end=None, last_all_sync=None, hosts=None):
        super(RemoteMirrorHandshakeMessage, self).__init__()
        self.type = REMOTE_MIRROR_HANDSHAKE
        self.id = id
        self.new_sync = new_sync
        self.sync_end = sync_end
        self.last_all_sync = last_all_sync
        self.hosts = hosts

    @staticmethod
    def deserialize(json_dict):
        msg = RemoteMirrorHandshakeMessage()
        msg.id = json_dict['id']
        msg.new_sync = json_dict['new_sync']
        msg.sync_end = json_dict['sync_end']
        msg.last_all_sync = json_dict['last_all_sync']
        msg.hosts = json_dict['hosts']
        return msg

