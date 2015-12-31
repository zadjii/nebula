from messages.SessionMessage import SessionMessage
from msg_codes import CLIENT_GET_CLOUD_HOST_RESPONSE as CLIENT_GET_CLOUD_HOST_RESPONSE
__author__ = 'Mike'


class ClientGetCloudHostResponse(SessionMessage):
    def __init__(self, session_id=None, cname=None, ip=None, port=None, wsport=None):
        super(ClientGetCloudHostResponse, self).__init__(session_id)
        self.type = CLIENT_GET_CLOUD_HOST_RESPONSE
        self.cname = cname
        self.ip = ip
        self.port = port
        self.wsport = wsport

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.cname = json_dict['cname']
        msg.ip = json_dict['ip']
        msg.port = json_dict['port']
        msg.wsport = json_dict['wsport']
        return msg
