# last generated 2015-12-31 02:30:42.343000
from messages import BaseMessage
from msg_codes import READ_FILE_RESPONSE as READ_FILE_RESPONSE
__author__ = 'Mike'


class ReadFileResponseMessage(BaseMessage):
    def __init__(self):
        super(ReadFileResponseMessage, self).__init__()
        self.type = READ_FILE_RESPONSE

    @staticmethod
    def deserialize(json_dict):
        msg = ReadFileResponseMessage()
        return msg

