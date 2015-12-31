# last generated 2015-12-31 02:30:42.336000
from messages import BaseMessage
from msg_codes import LIST_FILES_REQUEST as LIST_FILES_REQUEST
__author__ = 'Mike'


class ListFilesRequestMessage(BaseMessage):
    def __init__(self, sid=None, cname=None, fpath=None):
        super(ListFilesRequestMessage, self).__init__()
        self.type = LIST_FILES_REQUEST
        self.sid = sid
        self.cname = cname
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = ListFilesRequestMessage()
        msg.sid = json_dict['sid']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        return msg

