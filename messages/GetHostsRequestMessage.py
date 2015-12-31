# last generated 2015-12-31 02:30:42.320000
from messages import BaseMessage
from msg_codes import GET_HOSTS_REQUEST as GET_HOSTS_REQUEST
__author__ = 'Mike'


class GetHostsRequestMessage(BaseMessage):
    def __init__(self, id=None, cname=None):
        super(GetHostsRequestMessage, self).__init__()
        self.type = GET_HOSTS_REQUEST
        self.id = id
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = GetHostsRequestMessage()
        msg.id = json_dict['id']
        msg.cname = json_dict['cname']
        return msg

