# last generated 2016-12-30 20:11:44.004000
from messages import BaseMessage
from msg_codes import CLIENT_FILE_TRANSFER as CLIENT_FILE_TRANSFER
__author__ = 'Mike'


class ClientFileTransferMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None, fpath=None, fsize=None, isdir=None):
        super(ClientFileTransferMessage, self).__init__()
        self.type = CLIENT_FILE_TRANSFER
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.fpath = fpath
        self.fsize = fsize
        self.isdir = isdir

    @staticmethod
    def deserialize(json_dict):
        msg = ClientFileTransferMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        msg.fsize = json_dict['fsize']
        msg.isdir = json_dict['isdir']
        return msg

