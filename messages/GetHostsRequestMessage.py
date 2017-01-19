# last generated 2016-12-30 20:36:48.057000
from messages import BaseMessage
from msg_codes import GET_HOSTS_REQUEST as GET_HOSTS_REQUEST
__author__ = 'Mike'


class GetHostsRequestMessage(BaseMessage):
    def __init__(self, id=None, cloud_uname=None, cname=None):
        super(GetHostsRequestMessage, self).__init__()
        self.type = GET_HOSTS_REQUEST
        self.id = id
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = GetHostsRequestMessage()
        msg.id = json_dict['id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

