# last generated 2015-12-31 02:30:42.272000
from messages import BaseMessage
from msg_codes import FILE_IS_DIR_ERROR as FILE_IS_DIR_ERROR
__author__ = 'Mike'


class FileIsDirErrorMessage(BaseMessage):
    def __init__(self):
        super(FileIsDirErrorMessage, self).__init__()
        self.type = FILE_IS_DIR_ERROR

    @staticmethod
    def deserialize(json_dict):
        msg = FileIsDirErrorMessage()
        return msg

