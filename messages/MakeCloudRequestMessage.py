# last generated 2015-12-31 02:30:42.308000
from messages import BaseMessage
from msg_codes import MAKE_CLOUD_REQUEST as MAKE_CLOUD_REQUEST
__author__ = 'Mike'


class MakeCloudRequestMessage(BaseMessage):
    def __init__(self):
        super(MakeCloudRequestMessage, self).__init__()
        self.type = MAKE_CLOUD_REQUEST

    @staticmethod
    def deserialize(json_dict):
        msg = MakeCloudRequestMessage()
        return msg

