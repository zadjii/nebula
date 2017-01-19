# last generated 2016-12-30 20:36:47.952000
from messages import BaseMessage
from msg_codes import HOST_FILE_TRANSFER as HOST_FILE_TRANSFER
__author__ = 'Mike'


class HostFileTransferMessage(BaseMessage):
    def __init__(self, id=None, cloud_uname=None, cname=None, fpath=None, fsize=None, isdir=None):
        super(HostFileTransferMessage, self).__init__()
        self.type = HOST_FILE_TRANSFER
        self.id = id
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.fpath = fpath
        self.fsize = fsize
        self.isdir = isdir

    @staticmethod
    def deserialize(json_dict):
        msg = HostFileTransferMessage()
        msg.id = json_dict['id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        msg.fsize = json_dict['fsize']
        msg.isdir = json_dict['isdir']
        return msg

