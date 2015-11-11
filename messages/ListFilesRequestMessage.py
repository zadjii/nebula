from messages.util import make_ls_array
from messages.SessionMessage import SessionMessage
from msg_codes import LIST_FILES_REQUEST as LIST_FILES_REQUEST
__author__ = 'Mike'


class ListFilesRequestMessage(SessionMessage):
    def __init__(self, cname=None, session_id=None, fpath=None):
        super(ListFilesRequestMessage, self).__init__(cname, session_id)
        self.type = LIST_FILES_REQUEST
        self.fpath = fpath
        # self.ls = make_ls_array(fpath)

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.fpath = json_dict['fpath']
        # msg.ls = json_dict['ls']
        return msg
