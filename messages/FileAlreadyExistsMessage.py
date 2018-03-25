# last generated 2018-03-25 00:09:52.124000
from messages import BaseMessage
from msg_codes import FILE_ALREADY_EXISTS as FILE_ALREADY_EXISTS
__author__ = 'Mike'


class FileAlreadyExistsMessage(BaseMessage):
    def __init__(self, message=None):
        super(FileAlreadyExistsMessage, self).__init__()
        self.type = FILE_ALREADY_EXISTS
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = FileAlreadyExistsMessage()
        msg.message = json_dict['message']
        return msg

