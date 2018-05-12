# last generated 2018-05-11 00:36:23.505000
from messages import BaseMessage
from msg_codes import CLIENT_DELETE_RESPONSE as CLIENT_DELETE_RESPONSE
__author__ = 'Mike'


class ClientDeleteResponseMessage(BaseMessage):
    def __init__(self):
        super(ClientDeleteResponseMessage, self).__init__()
        self.type = CLIENT_DELETE_RESPONSE

    @staticmethod
    def deserialize(json_dict):
        msg = ClientDeleteResponseMessage()
        return msg

