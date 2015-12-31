# last generated 2015-12-31 02:30:42.348000
from messages import BaseMessage
from msg_codes import CLIENT_SESSION_ALERT as CLIENT_SESSION_ALERT
__author__ = 'Mike'


class ClientSessionAlertMessage(BaseMessage):
    def __init__(self, sid=None, uid=None, ip=None):
        super(ClientSessionAlertMessage, self).__init__()
        self.type = CLIENT_SESSION_ALERT
        self.sid = sid
        self.uid = uid
        self.ip = ip

    @staticmethod
    def deserialize(json_dict):
        msg = ClientSessionAlertMessage()
        msg.sid = json_dict['sid']
        msg.uid = json_dict['uid']
        msg.ip = json_dict['ip']
        return msg

