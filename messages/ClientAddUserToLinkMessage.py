# last generated 2018-05-15 00:01:17.073000
from messages import BaseMessage
from msg_codes import CLIENT_ADD_USER_TO_LINK as CLIENT_ADD_USER_TO_LINK
__author__ = 'Mike'


class ClientAddUserToLinkMessage(BaseMessage):
    def __init__(self, sid=None, link_string=None, user_id=None):
        super(ClientAddUserToLinkMessage, self).__init__()
        self.type = CLIENT_ADD_USER_TO_LINK
        self.sid = sid
        self.link_string = link_string
        self.user_id = user_id

    @staticmethod
    def deserialize(json_dict):
        msg = ClientAddUserToLinkMessage()
        msg.sid = json_dict['sid']
        msg.link_string = json_dict['link_string']
        msg.user_id = json_dict['user_id']
        return msg

