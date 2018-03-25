# last generated 2018-03-24 23:45:04.014000
from messages import BaseMessage
from msg_codes import CLIENT_GET_SHARED_PATHS_RESPONSE as CLIENT_GET_SHARED_PATHS_RESPONSE
__author__ = 'Mike'


class ClientGetSharedPathsResponseMessage(BaseMessage):
    def __init__(self, paths=None):
        super(ClientGetSharedPathsResponseMessage, self).__init__()
        self.type = CLIENT_GET_SHARED_PATHS_RESPONSE
        self.paths = paths

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetSharedPathsResponseMessage()
        msg.paths = json_dict['paths']
        return msg

