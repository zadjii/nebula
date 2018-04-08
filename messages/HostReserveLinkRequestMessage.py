# last generated 2018-04-08 02:13:50.681000
from messages import BaseMessage
from msg_codes import HOST_RESERVE_LINK_REQUEST as HOST_RESERVE_LINK_REQUEST
__author__ = 'Mike'


class HostReserveLinkRequestMessage(BaseMessage):
    def __init__(self, cloud_uname=None, cname=None):
        super(HostReserveLinkRequestMessage, self).__init__()
        self.type = HOST_RESERVE_LINK_REQUEST
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = HostReserveLinkRequestMessage()
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

