# last generated 2018-05-11 00:36:23.491000
from messages import BaseMessage
from msg_codes import CLIENT_DELETE_FILE_REQUEST as CLIENT_DELETE_FILE_REQUEST
__author__ = 'Mike'


class ClientDeleteFileRequestMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None, path=None):
        super(ClientDeleteFileRequestMessage, self).__init__()
        self.type = CLIENT_DELETE_FILE_REQUEST
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.path = path

    @staticmethod
    def deserialize(json_dict):
        msg = ClientDeleteFileRequestMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.path = json_dict['path']
        return msg

