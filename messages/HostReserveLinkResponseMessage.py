# last generated 2018-04-08 02:13:50.689000
from messages import BaseMessage
from msg_codes import HOST_RESERVE_LINK_RESPONSE as HOST_RESERVE_LINK_RESPONSE
__author__ = 'Mike'


class HostReserveLinkResponseMessage(BaseMessage):
    def __init__(self, link_string=None):
        super(HostReserveLinkResponseMessage, self).__init__()
        self.type = HOST_RESERVE_LINK_RESPONSE
        self.link_string = link_string

    @staticmethod
    def deserialize(json_dict):
        msg = HostReserveLinkResponseMessage()
        msg.link_string = json_dict['link_string']
        return msg

