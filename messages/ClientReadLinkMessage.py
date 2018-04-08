# last generated 2018-04-08 18:03:55.030000
from messages import BaseMessage
from msg_codes import CLIENT_READ_LINK as CLIENT_READ_LINK
__author__ = 'Mike'


class ClientReadLinkMessage(BaseMessage):
    def __init__(self, sid=None, link_string=None):
        super(ClientReadLinkMessage, self).__init__()
        self.type = CLIENT_READ_LINK
        self.sid = sid
        self.link_string = link_string

    @staticmethod
    def deserialize(json_dict):
        msg = ClientReadLinkMessage()
        msg.sid = json_dict['sid']
        msg.link_string = json_dict['link_string']
        return msg

