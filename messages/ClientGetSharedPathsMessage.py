# last generated 2018-03-24 23:21:54.197000
from messages import BaseMessage
from msg_codes import CLIENT_GET_SHARED_PATHS as CLIENT_GET_SHARED_PATHS
__author__ = 'Mike'


class ClientGetSharedPathsMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None):
        super(ClientGetSharedPathsMessage, self).__init__()
        self.type = CLIENT_GET_SHARED_PATHS
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetSharedPathsMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

