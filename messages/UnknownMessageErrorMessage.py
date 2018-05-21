# last generated 2018-05-21 02:02:42.387000
from messages import BaseMessage
from msg_codes import UNKNOWN_MESSAGE_ERROR as UNKNOWN_MESSAGE_ERROR
__author__ = 'Mike'


class UnknownMessageErrorMessage(BaseMessage):
    def __init__(self):
        super(UnknownMessageErrorMessage, self).__init__()
        self.type = UNKNOWN_MESSAGE_ERROR

    @staticmethod
    def deserialize(json_dict):
        msg = UnknownMessageErrorMessage()
        return msg

