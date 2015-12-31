# last generated 2015-12-31 02:30:42.311000
from messages import BaseMessage
from msg_codes import MAKE_CLOUD_RESPONSE as MAKE_CLOUD_RESPONSE
__author__ = 'Mike'


class MakeCloudResponseMessage(BaseMessage):
    def __init__(self):
        super(MakeCloudResponseMessage, self).__init__()
        self.type = MAKE_CLOUD_RESPONSE

    @staticmethod
    def deserialize(json_dict):
        msg = MakeCloudResponseMessage()
        return msg

