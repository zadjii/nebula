# last generated 2019-01-16 16:17:43.354000
from messages import BaseMessage
from msg_codes import FILE_SYNC_REQUEST as FILE_SYNC_REQUEST
__author__ = 'Mike'


class FileSyncRequestMessage(BaseMessage):
    def __init__(self, src_id=None, tgt_id=None, uname=None, cname=None, sync_start=None, sync_end=None):
        super(FileSyncRequestMessage, self).__init__()
        self.type = FILE_SYNC_REQUEST
        self.src_id = src_id
        self.tgt_id = tgt_id
        self.uname = uname
        self.cname = cname
        self.sync_start = sync_start
        self.sync_end = sync_end

    @staticmethod
    def deserialize(json_dict):
        msg = FileSyncRequestMessage()
        msg.src_id = json_dict['src_id']
        msg.tgt_id = json_dict['tgt_id']
        msg.uname = json_dict['uname']
        msg.cname = json_dict['cname']
        msg.sync_start = json_dict['sync_start']
        msg.sync_end = json_dict['sync_end']
        return msg

