from messages import make_stat_dict
from messages.SessionMessage import SessionMessage
from msg_codes import LIST_FILES_REQUEST as LIST_FILES_REQUEST
__author__ = 'Mike'


class ListFilesRequestMessage(SessionMessage):
    def __init__(self, cname=None, session_id=None, fpath=None):
        super(ListFilesRequestMessage, self).__init__(cname, session_id)
        self.type = LIST_FILES_REQUEST
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.fpath = json_dict['fpath']
        return msg
