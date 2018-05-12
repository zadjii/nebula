# last generated 2018-05-11 00:36:22.650000
from messages import BaseMessage
from msg_codes import DIR_IS_NOT_EMPTY as DIR_IS_NOT_EMPTY
__author__ = 'Mike'


class DirIsNotEmptyMessage(BaseMessage):
    def __init__(self, message=None):
        super(DirIsNotEmptyMessage, self).__init__()
        self.type = DIR_IS_NOT_EMPTY
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = DirIsNotEmptyMessage()
        msg.message = json_dict['message']
        return msg

