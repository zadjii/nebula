import json
from messages import BaseMessage
from msg_codes import GET_HOSTS_RESPONSE as GET_HOSTS_RESPONSE
__author__ = 'Mike'


class GetHostsResponseMessage(BaseMessage):
    def __init__(self, cloud=None):
        super(GetHostsResponseMessage, self).__init__()
        self.type = GET_HOSTS_RESPONSE
        if cloud is not None:
            self.cname = cloud.name
            hosts = cloud.hosts.all()
            host_jsons = []
            for host in hosts:
                host_obj = {
                    'ip': host.ip
                    , 'port': host.port
                    , 'id': host.id
                    , 'update': host.last_update
                    , 'hndshk': host.last_handshake
                }
                host_jsons.append(host_obj)
            self.hosts = host_jsons

    @staticmethod
    def deserialize(json_dict):
        msg = GetHostsResponseMessage()
        # msg.type = json_dict['type']
        # ^ I think it's assumed
        msg.cname = json_dict['cname']
        msg.hosts = json_dict['hosts']
        return msg

