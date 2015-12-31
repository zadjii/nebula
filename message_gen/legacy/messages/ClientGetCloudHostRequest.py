from messages.SessionMessage import SessionMessage
from msg_codes import CLIENT_GET_CLOUD_HOST_REQUEST as CLIENT_GET_CLOUD_HOST_REQUEST
__author__ = 'Mike'


class ClientGetCloudHostRequest(SessionMessage):
    def __init__(self, session_id=None, cname=None):
        super(ClientGetCloudHostRequest, self).__init__(session_id)
        self.type = CLIENT_GET_CLOUD_HOST_REQUEST
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.cname = json_dict['cname']
        return msg
