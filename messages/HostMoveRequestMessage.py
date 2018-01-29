# last generated 2018-01-02 01:50:01.278000
from messages import BaseMessage
from msg_codes import HOST_MOVE_REQUEST as HOST_MOVE_REQUEST
__author__ = 'Mike'


class HostMoveRequestMessage(BaseMessage):
    def __init__(self, my_id=None, ip=None, csr=None):
        super(HostMoveRequestMessage, self).__init__()
        self.type = HOST_MOVE_REQUEST
        self.my_id = my_id
        self.ip = ip
        self.csr = csr

    @staticmethod
    def deserialize(json_dict):
        msg = HostMoveRequestMessage()
        msg.my_id = json_dict['my_id']
        msg.ip = json_dict['ip']
        msg.csr = json_dict['csr']
        return msg

