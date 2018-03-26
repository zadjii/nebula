# last generated 2018-03-24 23:45:03.970000
from messages import BaseMessage
from msg_codes import CLIENT_MAKE_DIRECTORY_RESPONSE as CLIENT_MAKE_DIRECTORY_RESPONSE
__author__ = 'Mike'


class ClientMakeDirectoryResponseMessage(BaseMessage):
    def __init__(self):
        super(ClientMakeDirectoryResponseMessage, self).__init__()
        self.type = CLIENT_MAKE_DIRECTORY_RESPONSE

    @staticmethod
    def deserialize(json_dict):
        msg = ClientMakeDirectoryResponseMessage()
        return msg

