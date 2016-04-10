# last generated 2016-04-10 21:56:22.440000
from messages import BaseMessage
from msg_codes import NEW_HOST as NEW_HOST
__author__ = 'Mike'


class NewHostMessage(BaseMessage):
    def __init__(self, ipv6=None, port=None, wsport=None, hostname=None):
        super(NewHostMessage, self).__init__()
        self.type = NEW_HOST
        self.ipv6 = ipv6
        self.port = port
        self.wsport = wsport
        self.hostname = hostname

    @staticmethod
    def deserialize(json_dict):
        msg = NewHostMessage()
        msg.ipv6 = json_dict['ipv6']
        msg.port = json_dict['port']
        msg.wsport = json_dict['wsport']
        msg.hostname = json_dict['hostname']
        return msg

