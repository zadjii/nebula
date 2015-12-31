# last generated 2015-12-31 02:30:42.333000
from messages import BaseMessage
from messages.util import *
from msg_codes import STAT_FILE_RESPONSE as STAT_FILE_RESPONSE
__author__ = 'Mike'


class StatFileResponseMessage(BaseMessage):
    def __init__(self, sid=None, cname=None, fpath=None):
        super(StatFileResponseMessage, self).__init__()
        self.type = STAT_FILE_RESPONSE
        self.sid = sid
        self.cname = cname
        self.fpath = fpath
        self.stat = make_stat_dict(fpath)

    @staticmethod
    def deserialize(json_dict):
        msg = StatFileResponseMessage()
        msg.sid = json_dict['sid']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        msg.stat = json_dict['stat']
        return msg

