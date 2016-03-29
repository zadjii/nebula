# last generated 2016-03-29 02:40:02.067000
from messages import BaseMessage
from msg_codes import NEW_HOST as NEW_HOST
__author__ = 'Mike'


class NewHostMessage(BaseMessage):
    def __init__(self, ipv6=None, port=None, wsport=None):
        super(NewHostMessage, self).__init__()
        self.type = NEW_HOST
        self.ipv6 = ipv6
        self.port = port
        self.wsport = wsport

    @staticmethod
    def deserialize(json_dict):
        msg = NewHostMessage()
        msg.ipv6 = json_dict['ipv6']
        msg.port = json_dict['port']
        msg.wsport = json_dict['wsport']
        return msg

