from messages.util import make_stat_dict
from messages.SessionMessage import SessionMessage
from msg_codes import CLIENT_SESSION_ALERT as CLIENT_SESSION_ALERT
__author__ = 'Mike'


class ClientSessionAlertMessage(SessionMessage):
    def __init__(self, cname=None, session_id=None, user_id=None, ip=None):
        super(ClientSessionAlertMessage, self).__init__(cname, session_id)
        self.type = CLIENT_SESSION_ALERT
        self.uid = user_id
        self.ip = ip

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.uid = json_dict['uid']
        msg.ip = json_dict['ip']
        return msg
