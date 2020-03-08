# last generated 2020-03-08 06:37:03.539000
from messages import BaseMessage
from msg_codes import HOST_MOVE_REQUEST as HOST_MOVE_REQUEST
__author__ = 'Mike'


class HostMoveRequestMessage(BaseMessage):
    def __init__(self, my_id=None, ip=None, csr=None, port=None, wsport=None, hostname=None):
        super(HostMoveRequestMessage, self).__init__()
        self.type = HOST_MOVE_REQUEST
        self.my_id = my_id
        self.ip = ip
        self.csr = csr
        self.port = port
        self.wsport = wsport
        self.hostname = hostname

    @staticmethod
    def deserialize(json_dict):
        msg = HostMoveRequestMessage()
        msg.my_id = json_dict['my_id']
        msg.ip = json_dict['ip']
        msg.csr = json_dict['csr']
        msg.port = json_dict['port']
        msg.wsport = json_dict['wsport']
        msg.hostname = json_dict['hostname']
        return msg

