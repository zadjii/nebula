# last generated 2016-10-14 13:51:52.122000
from messages import BaseMessage
from msg_codes import GET_USER_ID as GET_USER_ID
__author__ = 'Mike'


class GetUserIdMessage(BaseMessage):
    def __init__(self, username=None):
        super(GetUserIdMessage, self).__init__()
        self.type = GET_USER_ID
        self.username = username

    @staticmethod
    def deserialize(json_dict):
        msg = GetUserIdMessage()
        msg.username = json_dict['username']
        return msg

