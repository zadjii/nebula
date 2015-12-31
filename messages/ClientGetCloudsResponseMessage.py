# last generated 2015-12-31 02:30:42.360000
from messages import BaseMessage
from msg_codes import CLIENT_GET_CLOUDS_RESPONSE as CLIENT_GET_CLOUDS_RESPONSE
__author__ = 'Mike'


class ClientGetCloudsResponseMessage(BaseMessage):
    def __init__(self, sid=None, owned=None, contrib=None):
        super(ClientGetCloudsResponseMessage, self).__init__()
        self.type = CLIENT_GET_CLOUDS_RESPONSE
        self.sid = sid
        self.owned = owned
        self.contrib = contrib

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetCloudsResponseMessage()
        msg.sid = json_dict['sid']
        msg.owned = json_dict['owned']
        msg.contrib = json_dict['contrib']
        return msg

