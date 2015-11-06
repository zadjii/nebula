import json
from messages import BaseMessage
from msg_codes import GO_RETRIEVE_HERE as GO_RETRIEVE_HERE
__author__ = 'Mike'


class GoRetrieveMessage(BaseMessage):
    def __init__(self, id=None, ip=None, port=None):
        super(GoRetrieveMessage, self).__init__()
        self.type = GO_RETRIEVE_HERE
        self.id = id
        self.ip = ip
        self.port = port

    @staticmethod
    def deserialize(json_dict):
        msg = GoRetrieveMessage()
        # msg.type = json_dict['type']
        # ^ I think it's assumed
        msg.id = json_dict['id']
        msg.ip = json_dict['ip']
        msg.port = json_dict['port']
        return msg

