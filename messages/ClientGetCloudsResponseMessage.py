# last generated 2015-12-31 02:30:42.360000
from messages import BaseMessage
from msg_codes import CLIENT_GET_CLOUDS_RESPONSE as CLIENT_GET_CLOUDS_RESPONSE
__author__ = 'Mike'


class ClientGetCloudsResponseMessage(BaseMessage):
    def __init__(self, sid=None, owned=None, shared=None):
        super(ClientGetCloudsResponseMessage, self).__init__()
        self.type = CLIENT_GET_CLOUDS_RESPONSE
        self.sid = sid
        self.owned = owned
        self.shared = shared

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetCloudsResponseMessage()
        msg.sid = json_dict['sid']
        msg.owned = json_dict['owned']
        msg.shared = json_dict['shared']
        return msg

