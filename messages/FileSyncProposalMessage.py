# last generated 2019-01-16 16:17:43.371000
from messages import BaseMessage
from msg_codes import FILE_SYNC_PROPOSAL as FILE_SYNC_PROPOSAL
__author__ = 'Mike'


class FileSyncProposalMessage(BaseMessage):
    def __init__(self, src_id=None, tgt_id=None, rel_path=None, tgt_path=None, change_type=None, is_dir=None, sync_time=None):
        super(FileSyncProposalMessage, self).__init__()
        self.type = FILE_SYNC_PROPOSAL
        self.src_id = src_id
        self.tgt_id = tgt_id
        self.rel_path = rel_path
        self.tgt_path = tgt_path
        self.change_type = change_type
        self.is_dir = is_dir
        self.sync_time = sync_time

    @staticmethod
    def deserialize(json_dict):
        msg = FileSyncProposalMessage()
        msg.src_id = json_dict['src_id']
        msg.tgt_id = json_dict['tgt_id']
        msg.rel_path = json_dict['rel_path']
        msg.tgt_path = json_dict['tgt_path']
        msg.change_type = json_dict['change_type']
        msg.is_dir = json_dict['is_dir']
        msg.sync_time = json_dict['sync_time']
        return msg

