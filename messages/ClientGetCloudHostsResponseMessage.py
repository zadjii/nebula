# last generated 2016-08-19 01:30:37.907000
from messages import BaseMessage
from msg_codes import CLIENT_GET_CLOUD_HOSTS_RESPONSE as CLIENT_GET_CLOUD_HOSTS_RESPONSE
__author__ = 'Mike'


class ClientGetCloudHostsResponseMessage(BaseMessage):
    def __init__(self, sid=None, hosts=None):
        super(ClientGetCloudHostsResponseMessage, self).__init__()
        self.type = CLIENT_GET_CLOUD_HOSTS_RESPONSE
        self.sid = sid
        self.hosts = hosts

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetCloudHostsResponseMessage()
        msg.sid = json_dict['sid']
        msg.hosts = json_dict['hosts']
        return msg

