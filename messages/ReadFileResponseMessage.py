# last generated 2016-01-08 05:31:00.013000
from messages import BaseMessage
from msg_codes import READ_FILE_RESPONSE as READ_FILE_RESPONSE
__author__ = 'Mike'


class ReadFileResponseMessage(BaseMessage):
    def __init__(self, sid=None, fpath=None, fsize=None):
        super(ReadFileResponseMessage, self).__init__()
        self.type = READ_FILE_RESPONSE
        self.sid = sid
        self.fpath = fpath
        self.fsize = fsize

    @staticmethod
    def deserialize(json_dict):
        msg = ReadFileResponseMessage()
        msg.sid = json_dict['sid']
        msg.fpath = json_dict['fpath']
        msg.fsize = json_dict['fsize']
        return msg

