from messages.util import make_stat_dict
from messages.SessionMessage import SessionMessage
from msg_codes import CLIENT_FILE_PUT as CLIENT_FILE_PUT
__author__ = 'Mike'


class ClientFilePutMessage(SessionMessage):
    def __init__(self, session_id=None, cname=None, fpath=None):
        super(ClientFilePutMessage, self).__init__(session_id)
        self.type = CLIENT_FILE_PUT
        self.fpath = fpath
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.fpath = json_dict['fpath']
        msg.cname = json_dict['cname']
        return msg
