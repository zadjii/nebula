# last generated 2016-09-05 19:18:53.833000
from messages import BaseMessage
from msg_codes import HOST_VERIFY_HOST_FAILURE as HOST_VERIFY_HOST_FAILURE
__author__ = 'Mike'


class HostVerifyHostFailureMessage(BaseMessage):
    def __init__(self, message=None):
        super(HostVerifyHostFailureMessage, self).__init__()
        self.type = HOST_VERIFY_HOST_FAILURE
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = HostVerifyHostFailureMessage()
        msg.message = json_dict['message']
        return msg

