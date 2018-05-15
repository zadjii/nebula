# last generated 2018-05-15 00:01:17.057000
from messages import BaseMessage
from msg_codes import CLIENT_SET_LINK_PERMISSIONS as CLIENT_SET_LINK_PERMISSIONS
__author__ = 'Mike'


class ClientSetLinkPermissionsMessage(BaseMessage):
    def __init__(self, sid=None, link_string=None, permissions=None):
        super(ClientSetLinkPermissionsMessage, self).__init__()
        self.type = CLIENT_SET_LINK_PERMISSIONS
        self.sid = sid
        self.link_string = link_string
        self.permissions = permissions

    @staticmethod
    def deserialize(json_dict):
        msg = ClientSetLinkPermissionsMessage()
        msg.sid = json_dict['sid']
        msg.link_string = json_dict['link_string']
        msg.permissions = json_dict['permissions']
        return msg

