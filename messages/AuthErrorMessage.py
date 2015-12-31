# last generated 2015-12-31 02:30:42.278000
from messages import BaseMessage
from msg_codes import AUTH_ERROR as AUTH_ERROR
__author__ = 'Mike'


class AuthErrorMessage(BaseMessage):
    def __init__(self):
        super(AuthErrorMessage, self).__init__()
        self.type = AUTH_ERROR

    @staticmethod
    def deserialize(json_dict):
        msg = AuthErrorMessage()
        return msg

