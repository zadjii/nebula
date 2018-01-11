# last generated 2015-12-31 02:30:42.322000
from messages import BaseMessage
from msg_codes import GET_HOSTS_RESPONSE as GET_HOSTS_RESPONSE
from datetime import datetime

__author__ = 'Mike'


class GetHostsResponseMessage(BaseMessage):
    def __init__(self, cloud=None):
        # type: (Cloud) -> None
        super(GetHostsResponseMessage, self).__init__()
        self.type = GET_HOSTS_RESPONSE
        self.cname = ''
        self.cloud_uname = ''
        self.hosts = []
        if cloud is not None:
            self.cname = cloud.name
            self.cloud_uname = cloud.uname()
            self.hosts = cloud.get_get_hosts_dict(active_only=False)


    @staticmethod
    def deserialize(json_dict):
        msg = GetHostsResponseMessage()
        msg.cname = json_dict['cname']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.hosts = json_dict['hosts']
        return msg

