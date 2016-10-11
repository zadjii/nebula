# last generated 2016-10-04 02:51:55.804000
from messages import BaseMessage
from msg_codes import CLIENT_SESSION_REFRESH as CLIENT_SESSION_REFRESH
__author__ = 'Mike'


class ClientSessionRefreshMessage(BaseMessage):
    def __init__(self, sid=None):
        super(ClientSessionRefreshMessage, self).__init__()
        self.type = CLIENT_SESSION_REFRESH
        self.sid = sid

    @staticmethod
    def deserialize(json_dict):
        msg = ClientSessionRefreshMessage()
        msg.sid = json_dict['sid']
        return msg

