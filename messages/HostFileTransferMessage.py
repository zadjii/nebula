import json
from messages import BaseMessage
from msg_codes import HOST_FILE_TRANSFER as HOST_FILE_TRANSFER
__author__ = 'Mike'


class HostFileTransferMessage(BaseMessage):
    def __init__(self, id=None, cname=None, fpath=None, fsize=None, isdir=None):
        super(HostFileTransferMessage, self).__init__()
        self.type = HOST_FILE_TRANSFER
        self.id = id
        self.cname = cname
        self.fpath = fpath
        self.fsize = fsize
        self.isdir = isdir

    @staticmethod
    def deserialize(json_dict):
        msg = HostFileTransferMessage()
        # msg.type = json_dict['type']
        # ^ I think it's assumed
        msg.id = json_dict['id']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        msg.fsize = json_dict['fsize']
        msg.isdir = json_dict['isdir']
        return msg

