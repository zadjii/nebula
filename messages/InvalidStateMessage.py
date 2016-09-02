# last generated 2016-08-27 22:21:59.460000
from messages import BaseMessage
from msg_codes import INVALID_STATE as INVALID_STATE
__author__ = 'Mike'


class InvalidStateMessage(BaseMessage):
    def __init__(self, message=None):
        super(InvalidStateMessage, self).__init__()
        self.type = INVALID_STATE
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = InvalidStateMessage()
        msg.message = json_dict['message']
        return msg

