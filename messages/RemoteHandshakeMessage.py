# last generated 2018-11-06 16:18:02.845000
from messages import BaseMessage
from msg_codes import REMOTE_HANDSHAKE as REMOTE_HANDSHAKE
__author__ = 'Mike'


class RemoteHandshakeMessage(BaseMessage):
    def __init__(self, id=None, new_sync=None, sync_end=None, last_all_sync=None, hosts=None):
        super(RemoteHandshakeMessage, self).__init__()
        self.type = REMOTE_HANDSHAKE
        self.id = id
        self.new_sync = new_sync
        self.sync_end = sync_end
        self.last_all_sync = last_all_sync
        self.hosts = hosts

    @staticmethod
    def deserialize(json_dict):
        msg = RemoteHandshakeMessage()
        msg.id = json_dict['id']
        msg.new_sync = json_dict['new_sync']
        msg.sync_end = json_dict['sync_end']
        msg.last_all_sync = json_dict['last_all_sync']
        msg.hosts = json_dict['hosts']
        return msg

