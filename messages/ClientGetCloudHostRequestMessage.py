# last generated 2015-12-31 02:30:42.362000
from messages import BaseMessage
from msg_codes import CLIENT_GET_CLOUD_HOST_REQUEST as CLIENT_GET_CLOUD_HOST_REQUEST
__author__ = 'Mike'


class ClientGetCloudHostRequestMessage(BaseMessage):
    def __init__(self, sid=None, cname=None):
        super(ClientGetCloudHostRequestMessage, self).__init__()
        self.type = CLIENT_GET_CLOUD_HOST_REQUEST
        self.sid = sid
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetCloudHostRequestMessage()
        msg.sid = json_dict['sid']
        msg.cname = json_dict['cname']
        return msg

