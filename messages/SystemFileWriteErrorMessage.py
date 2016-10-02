# last generated 2016-10-01 23:26:41.806000
from messages import BaseMessage
from msg_codes import SYSTEM_FILE_WRITE_ERROR as SYSTEM_FILE_WRITE_ERROR
__author__ = 'Mike'


class SystemFileWriteErrorMessage(BaseMessage):
    def __init__(self, message=None):
        super(SystemFileWriteErrorMessage, self).__init__()
        self.type = SYSTEM_FILE_WRITE_ERROR
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = SystemFileWriteErrorMessage()
        msg.message = json_dict['message']
        return msg

