# last generated 2016-10-01 23:26:41.975000
from messages import BaseMessage
from msg_codes import FILE_TRANSFER_SUCCESS as FILE_TRANSFER_SUCCESS
__author__ = 'Mike'


class FileTransferSuccessMessage(BaseMessage):
    def __init__(self, cloud_uname=None, cname=None, fpath=None):
        super(FileTransferSuccessMessage, self).__init__()
        self.type = FILE_TRANSFER_SUCCESS
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = FileTransferSuccessMessage()
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        return msg

