# last generated 2015-12-31 02:30:42.285000
from messages import BaseMessage
from msg_codes import ASSIGN_HOST_ID as ASSIGN_HOST_ID
__author__ = 'Mike'


class AssignHostIdMessage(BaseMessage):
    def __init__(self, id=None, key=None, cert=None):
        super(AssignHostIdMessage, self).__init__()
        self.type = ASSIGN_HOST_ID
        self.id = id
        self.key = key
        self.cert = cert

    @staticmethod
    def deserialize(json_dict):
        msg = AssignHostIdMessage()
        msg.id = json_dict['id']
        msg.key = json_dict['key']
        msg.cert = json_dict['cert']
        return msg

