# last generated 2018-05-15 00:06:17.182000
from messages import BaseMessage
from msg_codes import CLIENT_SET_LINK_PERMISSIONS_SUCCESS as CLIENT_SET_LINK_PERMISSIONS_SUCCESS
__author__ = 'Mike'


class ClientSetLinkPermissionsSuccessMessage(BaseMessage):
    def __init__(self):
        super(ClientSetLinkPermissionsSuccessMessage, self).__init__()
        self.type = CLIENT_SET_LINK_PERMISSIONS_SUCCESS

    @staticmethod
    def deserialize(json_dict):
        msg = ClientSetLinkPermissionsSuccessMessage()
        return msg

