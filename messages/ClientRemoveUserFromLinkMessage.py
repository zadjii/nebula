# last generated 2018-05-15 01:49:44.282000
from messages import BaseMessage
from msg_codes import CLIENT_REMOVE_USER_FROM_LINK as CLIENT_REMOVE_USER_FROM_LINK
__author__ = 'Mike'


class ClientRemoveUserFromLinkMessage(BaseMessage):
    def __init__(self, sid=None, link_string=None, user_id=None):
        super(ClientRemoveUserFromLinkMessage, self).__init__()
        self.type = CLIENT_REMOVE_USER_FROM_LINK
        self.sid = sid
        self.link_string = link_string
        self.user_id = user_id

    @staticmethod
    def deserialize(json_dict):
        msg = ClientRemoveUserFromLinkMessage()
        msg.sid = json_dict['sid']
        msg.link_string = json_dict['link_string']
        msg.user_id = json_dict['user_id']
        return msg

