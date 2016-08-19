# last generated 2016-08-19 01:30:37.897000
from messages import BaseMessage
from msg_codes import CLIENT_GET_CLOUD_HOSTS_REQUEST as CLIENT_GET_CLOUD_HOSTS_REQUEST
__author__ = 'Mike'


class ClientGetCloudHostsRequestMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None):
        super(ClientGetCloudHostsRequestMessage, self).__init__()
        self.type = CLIENT_GET_CLOUD_HOSTS_REQUEST
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetCloudHostsRequestMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

