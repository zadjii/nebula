# last generated 2018-05-15 13:51:37.410000
from messages import BaseMessage
from msg_codes import CLIENT_GET_LINK_PERMISSIONS_RESPONSE as CLIENT_GET_LINK_PERMISSIONS_RESPONSE
__author__ = 'Mike'


class ClientGetLinkPermissionsResponseMessage(BaseMessage):
    def __init__(self, permissions=None, users=None):
        super(ClientGetLinkPermissionsResponseMessage, self).__init__()
        self.type = CLIENT_GET_LINK_PERMISSIONS_RESPONSE
        self.permissions = permissions
        self.users = users

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetLinkPermissionsResponseMessage()
        msg.permissions = json_dict['permissions']
        msg.users = json_dict['users']
        return msg

