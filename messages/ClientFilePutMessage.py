from messages import make_stat_dict
from messages.SessionMessage import SessionMessage
from msg_codes import CLIENT_FILE_PUT as CLIENT_FILE_PUT
__author__ = 'Mike'


class ClientFilePutMessage(SessionMessage):
    def __init__(self, cname=None, session_id=None, fpath=None):
        super(ClientFilePutMessage, self).__init__(cname, session_id)
        self.type = CLIENT_FILE_PUT
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.fpath = json_dict['fpath']
        return msg
