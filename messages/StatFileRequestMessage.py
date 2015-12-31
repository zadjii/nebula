# last generated 2015-12-31 02:30:42.331000
from messages import BaseMessage
from msg_codes import STAT_FILE_REQUEST as STAT_FILE_REQUEST
__author__ = 'Mike'


class StatFileRequestMessage(BaseMessage):
    def __init__(self, sid=None, cname=None, fpath=None):
        super(StatFileRequestMessage, self).__init__()
        self.type = STAT_FILE_REQUEST
        self.sid = sid
        self.cname = cname
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = StatFileRequestMessage()
        msg.sid = json_dict['sid']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        return msg

