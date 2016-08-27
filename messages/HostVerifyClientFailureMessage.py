# last generated 2016-08-26 15:33:31.515000
from messages import BaseMessage
from msg_codes import HOST_VERIFY_CLIENT_FAILURE as HOST_VERIFY_CLIENT_FAILURE
__author__ = 'Mike'


class HostVerifyClientFailureMessage(BaseMessage):
    def __init__(self, message=None):
        super(HostVerifyClientFailureMessage, self).__init__()
        self.type = HOST_VERIFY_CLIENT_FAILURE
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = HostVerifyClientFailureMessage()
        msg.message = json_dict['message']
        return msg

