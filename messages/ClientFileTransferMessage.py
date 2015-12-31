# last generated 2015-12-31 02:30:42.355000
from messages import BaseMessage
from msg_codes import CLIENT_FILE_TRANSFER as CLIENT_FILE_TRANSFER
__author__ = 'Mike'


class ClientFileTransferMessage(BaseMessage):
    def __init__(self, sid=None, cname=None, fpath=None, fsize=None, isdir=None):
        super(ClientFileTransferMessage, self).__init__()
        self.type = CLIENT_FILE_TRANSFER
        self.sid = sid
        self.cname = cname
        self.fpath = fpath
        self.fsize = fsize
        self.isdir = isdir

    @staticmethod
    def deserialize(json_dict):
        msg = ClientFileTransferMessage()
        msg.sid = json_dict['sid']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        msg.fsize = json_dict['fsize']
        msg.isdir = json_dict['isdir']
        return msg

