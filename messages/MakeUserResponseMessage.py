# last generated 2015-12-31 02:30:42.315000
from messages import BaseMessage
from msg_codes import MAKE_USER_RESPONSE as MAKE_USER_RESPONSE
__author__ = 'Mike'


class MakeUserResponseMessage(BaseMessage):
    def __init__(self):
        super(MakeUserResponseMessage, self).__init__()
        self.type = MAKE_USER_RESPONSE

    @staticmethod
    def deserialize(json_dict):
        msg = MakeUserResponseMessage()
        return msg

