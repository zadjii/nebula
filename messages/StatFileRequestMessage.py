import json
from messages.SessionMessage import SessionMessage
from msg_codes import STAT_FILE_REQUEST as STAT_FILE_REQUEST
__author__ = 'Mike'


class StatFileRequestMessage(SessionMessage):
    def __init__(self, cname=None, session_id=None, fpath=None):
        super(StatFileRequestMessage, self).__init__(cname, session_id)
        self.type = STAT_FILE_REQUEST
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.fpath = json_dict['fpath']
        return msg

