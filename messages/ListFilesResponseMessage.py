from messages.util import make_ls_array
from messages.util import make_stat_dict, make_ls_array
from messages.SessionMessage import SessionMessage
from msg_codes import LIST_FILES_RESPONSE as LIST_FILES_RESPONSE
__author__ = 'Mike'


class ListFilesResponseMessage(SessionMessage):
    def __init__(self, cname=None, session_id=None, rel_path=None, fpath=None):
        super(ListFilesResponseMessage, self).__init__(cname, session_id)
        self.type = LIST_FILES_RESPONSE
        self.fpath = rel_path
        self.stat = make_stat_dict(fpath)
        self.ls = make_ls_array(fpath)

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.fpath = json_dict['fpath']
        msg.stat = json_dict['stat']
        msg.ls = json_dict['ls']
        return msg
