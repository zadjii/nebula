from messages import make_stat_dict
from messages.SessionMessage import SessionMessage
from msg_codes import CLIENT_SESSION_REQUEST as CLIENT_SESSION_REQUEST
__author__ = 'Mike'


class ClientSessionRequestMessage(SessionMessage):
    def __init__(self, cname=None, session_id=None, username=None, password=None):
        super(ClientSessionRequestMessage, self).__init__(cname, session_id)
        self.type = CLIENT_SESSION_REQUEST
        self.uname = username
        self.passw = password

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.uname = json_dict['uname']
        msg.passw = json_dict['passw']
        return msg
