import json
from messages import BaseMessage
from msg_codes import HOST_FILE_PUSH as HOST_FILE_PUSH
__author__ = 'Mike'


class HostFilePushMessage(BaseMessage):
    def __init__(self, tid=None, cname=None, fpath=None):
        super(HostFilePushMessage, self).__init__()
        self.type = HOST_FILE_PUSH
        self.tid = tid
        self.cname = cname
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = HostFilePushMessage()
        # msg.type = json_dict['type']
        # ^ I think it's assumed
        msg.tid = json_dict['tid']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        return msg

