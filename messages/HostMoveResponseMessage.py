# last generated 2018-01-02 01:50:01.285000
from messages import BaseMessage
from msg_codes import HOST_MOVE_RESPONSE as HOST_MOVE_RESPONSE
__author__ = 'Mike'


class HostMoveResponseMessage(BaseMessage):
    def __init__(self, host_id=None, crt=None):
        super(HostMoveResponseMessage, self).__init__()
        self.type = HOST_MOVE_RESPONSE
        self.host_id = host_id
        self.crt = crt

    @staticmethod
    def deserialize(json_dict):
        msg = HostMoveResponseMessage()
        msg.host_id = json_dict['host_id']
        msg.crt = json_dict['crt']
        return msg

