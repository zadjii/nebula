# last generated 2016-12-30 20:11:44.027000
from messages import BaseMessage
from msg_codes import CLIENT_GET_CLOUD_HOST_REQUEST as CLIENT_GET_CLOUD_HOST_REQUEST
__author__ = 'Mike'


class ClientGetCloudHostRequestMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None):
        super(ClientGetCloudHostRequestMessage, self).__init__()
        self.type = CLIENT_GET_CLOUD_HOST_REQUEST
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetCloudHostRequestMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

