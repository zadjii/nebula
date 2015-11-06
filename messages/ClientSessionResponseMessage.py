from messages import make_stat_dict
from messages.SessionMessage import SessionMessage
from msg_codes import CLIENT_SESSION_RESPONSE as CLIENT_SESSION_RESPONSE
__author__ = 'Mike'


class ClientSessionResponseMessage(SessionMessage):
    def __init__(self, cname=None, session_id=None, ip=None, port=None):
        super(ClientSessionResponseMessage, self).__init__(cname, session_id)
        self.type = CLIENT_SESSION_RESPONSE
        self.ip = ip
        self.port = port

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.ip = json_dict['ip']
        msg.port = json_dict['port']
        return msg
