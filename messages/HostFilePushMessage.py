# last generated 2016-12-30 20:11:43.924000
from messages import BaseMessage
from msg_codes import HOST_FILE_PUSH as HOST_FILE_PUSH
__author__ = 'Mike'


class HostFilePushMessage(BaseMessage):
    def __init__(self, tid=None, cloud_uname=None, cname=None, fpath=None):
        super(HostFilePushMessage, self).__init__()
        self.type = HOST_FILE_PUSH
        self.tid = tid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = HostFilePushMessage()
        msg.tid = json_dict['tid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        return msg

