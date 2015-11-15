from messages import BaseMessage
from messages.util import make_stat_dict
from messages.BaseMessage import BaseMessage
from msg_codes import CLIENT_SESSION_REQUEST as CLIENT_SESSION_REQUEST
__author__ = 'Mike'


class ClientSessionRequestMessage(BaseMessage):
    def __init__(self, username=None, password=None):
        super(ClientSessionRequestMessage, self).__init__()
        self.type = CLIENT_SESSION_REQUEST
        # self.cname = cname
        self.uname = username
        self.passw = password

    @staticmethod
    def deserialize(json_dict):
        msg = ClientSessionRequestMessage()
        # msg.cname = json_dict['cname']
        msg.uname = json_dict['uname']
        msg.passw = json_dict['passw']
        return msg
