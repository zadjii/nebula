# last generated 2018-03-24 23:45:03.999000
from messages import BaseMessage
from msg_codes import CLIENT_GET_PERMISSIONS_RESPONSE as CLIENT_GET_PERMISSIONS_RESPONSE
__author__ = 'Mike'


class ClientGetPermissionsResponseMessage(BaseMessage):
    def __init__(self, permission=None):
        super(ClientGetPermissionsResponseMessage, self).__init__()
        self.type = CLIENT_GET_PERMISSIONS_RESPONSE
        self.permission = permission

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetPermissionsResponseMessage()
        msg.permission = json_dict['permission']
        return msg

