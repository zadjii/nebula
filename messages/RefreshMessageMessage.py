# last generated 2016-12-19 16:19:33.715000
from messages import BaseMessage
from msg_codes import REFRESH_MESSAGE as REFRESH_MESSAGE
__author__ = 'Mike'


class RefreshMessageMessage(BaseMessage):
    def __init__(self):
        super(RefreshMessageMessage, self).__init__()
        self.type = REFRESH_MESSAGE

    @staticmethod
    def deserialize(json_dict):
        msg = RefreshMessageMessage()
        return msg

