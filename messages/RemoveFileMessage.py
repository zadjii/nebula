# last generated 2015-12-31 02:30:42.326000
from messages import BaseMessage
from msg_codes import REMOVE_FILE as REMOVE_FILE
__author__ = 'Mike'


class RemoveFileMessage(BaseMessage):
    def __init__(self, id=None, cname=None, fpath=None):
        super(RemoveFileMessage, self).__init__()
        self.type = REMOVE_FILE
        self.id = id
        self.cname = cname
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = RemoveFileMessage()
        msg.id = json_dict['id']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        return msg

