# last generated 2016-04-10 21:56:22.756000
from messages import BaseMessage
from msg_codes import GET_ACTIVE_HOSTS_RESPONSE as GET_ACTIVE_HOSTS_RESPONSE
__author__ = 'Mike'


class GetActiveHostsResponseMessage(BaseMessage):
    def __init__(self, cloud=None):
        super(GetActiveHostsResponseMessage, self).__init__()
        self.type = GET_ACTIVE_HOSTS_RESPONSE
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
                    , 'hostname': host.hostname
                }
                host_jsons.append(host_obj)
            self.hosts = host_jsons

    @staticmethod
    def deserialize(json_dict):
        msg = GetActiveHostsResponseMessage()
        msg.cname = json_dict['cname']
        msg.hosts = json_dict['hosts']
        return msg

