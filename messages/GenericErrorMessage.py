# last generated 2015-12-31 02:30:42.281000
from messages import BaseMessage
from msg_codes import GENERIC_ERROR as GENERIC_ERROR
__author__ = 'Mike'


class GenericErrorMessage(BaseMessage):
    def __init__(self):
        super(GenericErrorMessage, self).__init__()
        self.type = GENERIC_ERROR

    @staticmethod
    def deserialize(json_dict):
        msg = GenericErrorMessage()
        return msg

