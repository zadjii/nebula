# last generated 2018-04-08 02:13:50.697000
from messages import BaseMessage
from msg_codes import CLIENT_GET_LINK_HOST as CLIENT_GET_LINK_HOST
__author__ = 'Mike'


class ClientGetLinkHostMessage(BaseMessage):
    def __init__(self, sid=None, link_string=None):
        super(ClientGetLinkHostMessage, self).__init__()
        self.type = CLIENT_GET_LINK_HOST
        self.sid = sid
        self.link_string = link_string

    @staticmethod
    def deserialize(json_dict):
        msg = ClientGetLinkHostMessage()
        msg.sid = json_dict['sid']
        msg.link_string = json_dict['link_string']
        return msg

