# last generated 2016-12-30 20:11:43.917000
from messages import BaseMessage
from msg_codes import REMOVE_FILE as REMOVE_FILE
__author__ = 'Mike'


class RemoveFileMessage(BaseMessage):
    def __init__(self, id=None, cloud_uname=None, cname=None, fpath=None):
        super(RemoveFileMessage, self).__init__()
        self.type = REMOVE_FILE
        self.id = id
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = RemoveFileMessage()
        msg.id = json_dict['id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        return msg

