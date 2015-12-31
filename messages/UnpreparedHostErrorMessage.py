# last generated 2015-12-31 02:30:42.275000
from messages import BaseMessage
from msg_codes import UNPREPARED_HOST_ERROR as UNPREPARED_HOST_ERROR
__author__ = 'Mike'


class UnpreparedHostErrorMessage(BaseMessage):
    def __init__(self):
        super(UnpreparedHostErrorMessage, self).__init__()
        self.type = UNPREPARED_HOST_ERROR

    @staticmethod
    def deserialize(json_dict):
        msg = UnpreparedHostErrorMessage()
        return msg

