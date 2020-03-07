# last generated 2020-03-06 02:33:22.608000
from messages import BaseMessage
from msg_codes import FILE_SYNC_COMPLETE as FILE_SYNC_COMPLETE
__author__ = 'Mike'


class FileSyncCompleteMessage(BaseMessage):
    def __init__(self):
        super(FileSyncCompleteMessage, self).__init__()
        self.type = FILE_SYNC_COMPLETE

    @staticmethod
    def deserialize(json_dict):
        msg = FileSyncCompleteMessage()
        return msg

