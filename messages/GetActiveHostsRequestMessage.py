# last generated 2016-12-30 20:11:44.038000
from messages import BaseMessage
from msg_codes import GET_ACTIVE_HOSTS_REQUEST as GET_ACTIVE_HOSTS_REQUEST
__author__ = 'Mike'


class GetActiveHostsRequestMessage(BaseMessage):
    def __init__(self, id=None, cloud_uname=None, cname=None):
        super(GetActiveHostsRequestMessage, self).__init__()
        self.type = GET_ACTIVE_HOSTS_REQUEST
        self.id = id
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = GetActiveHostsRequestMessage()
        msg.id = json_dict['id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

