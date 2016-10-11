# last generated 2016-10-10 23:18:11.702000
from messages import BaseMessage
from msg_codes import MIRROR_SUCCESS as MIRROR_SUCCESS
__author__ = 'Mike'


class MirrorSuccessMessage(BaseMessage):
    def __init__(self):
        super(MirrorSuccessMessage, self).__init__()
        self.type = MIRROR_SUCCESS

    @staticmethod
    def deserialize(json_dict):
        msg = MirrorSuccessMessage()
        return msg

