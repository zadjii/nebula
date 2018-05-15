# last generated 2018-05-15 00:01:15.457000
from messages import BaseMessage
from msg_codes import LINK_DOES_NOT_EXIST as LINK_DOES_NOT_EXIST
__author__ = 'Mike'


class LinkDoesNotExistMessage(BaseMessage):
    def __init__(self, message=None):
        super(LinkDoesNotExistMessage, self).__init__()
        self.type = LINK_DOES_NOT_EXIST
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = LinkDoesNotExistMessage()
        msg.message = json_dict['message']
        return msg

