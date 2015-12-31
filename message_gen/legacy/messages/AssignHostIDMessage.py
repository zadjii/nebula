import json
from messages import BaseMessage
from msg_codes import ASSIGN_HOST_ID as ASSIGN_HOST_ID
__author__ = 'Mike'


class AssignHostIDMessage(BaseMessage):
    def __init__(self, id=None, key=None, cert=None):
        super(AssignHostIDMessage, self).__init__()
        self.type = ASSIGN_HOST_ID
        self.id = id
        self.key = key
        self.cert = cert

    @staticmethod
    def deserialize(json_dict):
        msg = AssignHostIDMessage()
        # msg.type = json_dict['type']
        # ^ I think it's assumed
        msg.id = json_dict['id']
        msg.key = json_dict['key']
        msg.cert = json_dict['cert']
        return msg

