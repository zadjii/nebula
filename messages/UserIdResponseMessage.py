# last generated 2016-10-14 13:51:52.127000
from messages import BaseMessage
from msg_codes import USER_ID_RESPONSE as USER_ID_RESPONSE
__author__ = 'Mike'


class UserIdResponseMessage(BaseMessage):
    def __init__(self, username=None, id=None):
        super(UserIdResponseMessage, self).__init__()
        self.type = USER_ID_RESPONSE
        self.username = username
        self.id = id

    @staticmethod
    def deserialize(json_dict):
        msg = UserIdResponseMessage()
        msg.username = json_dict['username']
        msg.id = json_dict['id']
        return msg

