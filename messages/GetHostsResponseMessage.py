# last generated 2015-12-31 02:30:42.322000
from messages import BaseMessage
from msg_codes import GET_HOSTS_RESPONSE as GET_HOSTS_RESPONSE
from datetime import datetime
__author__ = 'Mike'


class GetHostsResponseMessage(BaseMessage):
    def __init__(self, cloud=None):
        super(GetHostsResponseMessage, self).__init__()
        self.type = GET_HOSTS_RESPONSE
        if cloud is not None:
            self.cname = cloud.name
            hosts = cloud.active_hosts()
            host_jsons = []
            for host in hosts:
                host_obj = {
                    'ip': host.ipv6
                    , 'port': host.port
                    , 'wsport': host.ws_port
                    , 'id': host.id
                    , 'update': host.last_update
                    , 'hndshk': host.last_handshake.isoformat()
                }
                host_jsons.append(host_obj)
            self.hosts = host_jsons

    @staticmethod
    def deserialize(json_dict):
        msg = GetHostsResponseMessage()
        msg.cname = json_dict['cname']
        msg.hosts = json_dict['hosts']
        return msg

