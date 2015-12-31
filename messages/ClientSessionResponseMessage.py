# last generated 2015-12-31 02:30:42.350000
from messages import BaseMessage
from msg_codes import CLIENT_SESSION_RESPONSE as CLIENT_SESSION_RESPONSE
__author__ = 'Mike'


class ClientSessionResponseMessage(BaseMessage):
    def __init__(self, sid=None):
        super(ClientSessionResponseMessage, self).__init__()
        self.type = CLIENT_SESSION_RESPONSE
        self.sid = sid

    @staticmethod
    def deserialize(json_dict):
        msg = ClientSessionResponseMessage()
        msg.sid = json_dict['sid']
        return msg

