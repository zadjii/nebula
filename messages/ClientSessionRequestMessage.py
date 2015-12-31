# last generated 2015-12-31 02:30:42.345000
from messages import BaseMessage
from msg_codes import CLIENT_SESSION_REQUEST as CLIENT_SESSION_REQUEST
__author__ = 'Mike'


class ClientSessionRequestMessage(BaseMessage):
    def __init__(self, uname=None, passw=None):
        super(ClientSessionRequestMessage, self).__init__()
        self.type = CLIENT_SESSION_REQUEST
        self.uname = uname
        self.passw = passw

    @staticmethod
    def deserialize(json_dict):
        msg = ClientSessionRequestMessage()
        msg.uname = json_dict['uname']
        msg.passw = json_dict['passw']
        return msg

