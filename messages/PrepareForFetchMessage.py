import json
from messages import BaseMessage
from msg_codes import PREPARE_FOR_FETCH as PREPARE_FOR_FETCH
__author__ = 'Mike'


class PrepareForFetchMessage(BaseMessage):
    def __init__(self, id=None, cname=None, ip=None):
        super(PrepareForFetchMessage, self).__init__()
        self.type = PREPARE_FOR_FETCH
        self.id = id
        self.cname = cname
        self.ip = ip

    @staticmethod
    def deserialize(json_dict):
        msg = PrepareForFetchMessage()
        # msg.type = json_dict['type']
        # ^ I think it's assumed
        msg.id = json_dict['id']
        msg.cname = json_dict['cname']
        msg.ip = json_dict['ip']
        return msg

