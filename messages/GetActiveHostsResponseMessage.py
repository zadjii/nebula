# last generated 2016-04-10 21:56:22.756000
from messages import BaseMessage
from msg_codes import GET_ACTIVE_HOSTS_RESPONSE as GET_ACTIVE_HOSTS_RESPONSE

__author__ = 'Mike'


class GetActiveHostsResponseMessage(BaseMessage):
    def __init__(self, cloud=None):
        # type: (Cloud) -> None
        super(GetActiveHostsResponseMessage, self).__init__()
        self.type = GET_ACTIVE_HOSTS_RESPONSE
        self.cname = ''
        self.cloud_uname = ''
        self.hosts = []
        if cloud is not None:
            self.cname = cloud.name
            self.cloud_uname = cloud.uname()
            self.hosts = cloud.get_get_hosts_dict(active_only=True)


    @staticmethod
    def deserialize(json_dict):
        msg = GetActiveHostsResponseMessage()
        msg.cname = json_dict['cname']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.hosts = json_dict['hosts']
        return msg

