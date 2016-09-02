# last generated 2016-08-30 02:47:27.049000
from messages import BaseMessage
from msg_codes import INVALID_PERMISSIONS as INVALID_PERMISSIONS
__author__ = 'Mike'


class InvalidPermissionsMessage(BaseMessage):
    def __init__(self, message=None):
        super(InvalidPermissionsMessage, self).__init__()
        self.type = INVALID_PERMISSIONS
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = InvalidPermissionsMessage()
        msg.message = json_dict['message']
        return msg

