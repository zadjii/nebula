# last generated 2018-05-15 13:51:37.397000
from messages import BaseMessage
from msg_codes import CLIENT_GET_LINK_PERMISSIONS_REQUEST as CLIENT_GET_LINK_PERMISSIONS_REQUEST
__author__ = 'Mike'


class ClientGetLinkPermissionsRequestMessage(BaseMessage):
    def __init__(self, sid=None, link_string=None):
        super(ClientGetLinkPermissionsRequestMessage, self).__init__()
        self.type = CLIENT_GET_LINK_PERMISSIONS_REQUEST
        self.sid = sid
        self.link_string = link_string

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetLinkPermissionsRequestMessage()
        msg.sid = json_dict['sid']
        msg.link_string = json_dict['link_string']
        return msg

