from messages.SessionMessage import SessionMessage
from msg_codes import CLIENT_GET_CLOUDS_RESPONSE as CLIENT_GET_CLOUDS_RESPONSE
__author__ = 'Mike'


class ClientGetCloudsResponse(SessionMessage):
    def __init__(self, session_id=None, owned=None, contrib=None):
        super(ClientGetCloudsResponse, self).__init__(session_id)
        self.type = CLIENT_GET_CLOUDS_RESPONSE
        self.owned = owned
        self.contrib = contrib

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.owned = json_dict['owned']
        msg.contrib = json_dict['contrib']
        return msg
