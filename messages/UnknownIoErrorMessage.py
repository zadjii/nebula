# last generated 2016-10-01 23:26:41.810000
from messages import BaseMessage
from msg_codes import UNKNOWN_IO_ERROR as UNKNOWN_IO_ERROR
__author__ = 'Mike'


class UnknownIoErrorMessage(BaseMessage):
    def __init__(self, message=None):
        super(UnknownIoErrorMessage, self).__init__()
        self.type = UNKNOWN_IO_ERROR
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = UnknownIoErrorMessage()
        msg.message = json_dict['message']
        return msg

