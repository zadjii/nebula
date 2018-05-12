# last generated 2018-05-11 00:36:23.498000
from messages import BaseMessage
from msg_codes import CLIENT_DELETE_DIR_REQUEST as CLIENT_DELETE_DIR_REQUEST
__author__ = 'Mike'


class ClientDeleteDirRequestMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None, path=None, recursive=None):
        super(ClientDeleteDirRequestMessage, self).__init__()
        self.type = CLIENT_DELETE_DIR_REQUEST
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.path = path
        self.recursive = recursive

    @staticmethod
    def deserialize(json_dict):
        msg = ClientDeleteDirRequestMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.path = json_dict['path']
        msg.recursive = json_dict['recursive']
        return msg

