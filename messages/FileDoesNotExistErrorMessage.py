# last generated 2016-01-09 19:18:46.523000
from messages import BaseMessage
from msg_codes import FILE_DOES_NOT_EXIST_ERROR as FILE_DOES_NOT_EXIST_ERROR
__author__ = 'Mike'


class FileDoesNotExistErrorMessage(BaseMessage):
    def __init__(self):
        super(FileDoesNotExistErrorMessage, self).__init__()
        self.type = FILE_DOES_NOT_EXIST_ERROR

    @staticmethod
    def deserialize(json_dict):
        msg = FileDoesNotExistErrorMessage()
        return msg

