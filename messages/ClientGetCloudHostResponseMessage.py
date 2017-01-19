# last generated 2016-12-30 20:11:44.032000
from messages import BaseMessage
from msg_codes import CLIENT_GET_CLOUD_HOST_RESPONSE as CLIENT_GET_CLOUD_HOST_RESPONSE
__author__ = 'Mike'


class ClientGetCloudHostResponseMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None, ip=None, port=None, wsport=None):
        super(ClientGetCloudHostResponseMessage, self).__init__()
        self.type = CLIENT_GET_CLOUD_HOST_RESPONSE
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.ip = ip
        self.port = port
        self.wsport = wsport

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetCloudHostResponseMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.ip = json_dict['ip']
        msg.port = json_dict['port']
        msg.wsport = json_dict['wsport']
        return msg

