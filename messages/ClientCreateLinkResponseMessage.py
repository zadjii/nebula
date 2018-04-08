# last generated 2018-04-08 17:56:17.495000
from messages import BaseMessage
from msg_codes import CLIENT_CREATE_LINK_RESPONSE as CLIENT_CREATE_LINK_RESPONSE
__author__ = 'Mike'


class ClientCreateLinkResponseMessage(BaseMessage):
    def __init__(self, link_string=None):
        super(ClientCreateLinkResponseMessage, self).__init__()
        self.type = CLIENT_CREATE_LINK_RESPONSE
        self.link_string = link_string

    @staticmethod
    def deserialize(json_dict):
        msg = ClientCreateLinkResponseMessage()
        msg.link_string = json_dict['link_string']
        return msg

