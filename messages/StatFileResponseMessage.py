from messages.util import make_stat_dict
from messages.SessionMessage import SessionMessage
from msg_codes import STAT_FILE_RESPONSE as STAT_FILE_RESPONSE
__author__ = 'Mike'


class StatFileResponseMessage(SessionMessage):
    def __init__(self, cname=None, session_id=None, fpath=None):
        super(StatFileResponseMessage, self).__init__(cname, session_id)
        self.type = STAT_FILE_RESPONSE
        self.fpath = fpath
        self.stat = make_stat_dict(fpath)

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.fpath = json_dict['fpath']
        msg.stat = json_dict['stat']
        return msg


