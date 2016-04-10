# last generated 2016-04-10 21:56:22.749000
from messages import BaseMessage
from msg_codes import GET_ACTIVE_HOSTS_REQUEST as GET_ACTIVE_HOSTS_REQUEST
__author__ = 'Mike'


class GetActiveHostsRequestMessage(BaseMessage):
    def __init__(self, id=None, cname=None):
        super(GetActiveHostsRequestMessage, self).__init__()
        self.type = GET_ACTIVE_HOSTS_REQUEST
        self.id = id
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = GetActiveHostsRequestMessage()
        msg.id = json_dict['id']
        msg.cname = json_dict['cname']
        return msg

