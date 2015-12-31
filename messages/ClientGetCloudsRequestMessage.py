# last generated 2015-12-31 02:30:42.357000
from messages import BaseMessage
from msg_codes import CLIENT_GET_CLOUDS_REQUEST as CLIENT_GET_CLOUDS_REQUEST
__author__ = 'Mike'


class ClientGetCloudsRequestMessage(BaseMessage):
    def __init__(self, sid=None):
        super(ClientGetCloudsRequestMessage, self).__init__()
        self.type = CLIENT_GET_CLOUDS_REQUEST
        self.sid = sid

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetCloudsRequestMessage()
        msg.sid = json_dict['sid']
        return msg

