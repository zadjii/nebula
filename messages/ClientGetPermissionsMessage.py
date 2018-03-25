# last generated 2018-03-24 23:21:54.189000
from messages import BaseMessage
from msg_codes import CLIENT_GET_PERMISSIONS as CLIENT_GET_PERMISSIONS
__author__ = 'Mike'


class ClientGetPermissionsMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None, path=None):
        super(ClientGetPermissionsMessage, self).__init__()
        self.type = CLIENT_GET_PERMISSIONS
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.path = path

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetPermissionsMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.path = json_dict['path']
        return msg

