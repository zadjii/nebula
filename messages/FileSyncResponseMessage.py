# last generated 2018-11-06 16:18:05.303000
from messages import BaseMessage
from msg_codes import FILE_SYNC_RESPONSE as FILE_SYNC_RESPONSE
__author__ = 'Mike'


class FileSyncResponseMessage(BaseMessage):
    def __init__(self, resp_type=None):
        super(FileSyncResponseMessage, self).__init__()
        self.type = FILE_SYNC_RESPONSE
        self.resp_type = resp_type

    @staticmethod
    def deserialize(json_dict):
        msg = FileSyncResponseMessage()
        msg.resp_type = json_dict['resp_type']
        return msg

