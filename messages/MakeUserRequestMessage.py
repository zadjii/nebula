# last generated 2015-12-31 02:30:42.313000
from messages import BaseMessage
from msg_codes import MAKE_USER_REQUEST as MAKE_USER_REQUEST
__author__ = 'Mike'


class MakeUserRequestMessage(BaseMessage):
    def __init__(self):
        super(MakeUserRequestMessage, self).__init__()
        self.type = MAKE_USER_REQUEST

    @staticmethod
    def deserialize(json_dict):
        msg = MakeUserRequestMessage()
        return msg

