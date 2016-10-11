# last generated 2016-10-10 23:18:11.379000
from messages import BaseMessage
from msg_codes import MIRROR_FAILURE as MIRROR_FAILURE
__author__ = 'Mike'


class MirrorFailureMessage(BaseMessage):
    def __init__(self, message=None):
        super(MirrorFailureMessage, self).__init__()
        self.type = MIRROR_FAILURE
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = MirrorFailureMessage()
        msg.message = json_dict['message']
        return msg

