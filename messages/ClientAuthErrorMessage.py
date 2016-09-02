# last generated 2016-08-27 22:21:59.465000
from messages import BaseMessage
from msg_codes import CLIENT_AUTH_ERROR as CLIENT_AUTH_ERROR
__author__ = 'Mike'


class ClientAuthErrorMessage(BaseMessage):
    def __init__(self, message=None):
        super(ClientAuthErrorMessage, self).__init__()
        self.type = CLIENT_AUTH_ERROR
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = ClientAuthErrorMessage()
        msg.message = json_dict['message']
        return msg

