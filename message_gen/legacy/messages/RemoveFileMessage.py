import json
from messages import BaseMessage
from msg_codes import REMOVE_FILE as REMOVE_FILE
__author__ = 'Mike'


class RemoveFileMessage(BaseMessage):
    def __init__(self, id=None, cname=None, root=None):
        super(RemoveFileMessage, self).__init__()
        self.type = REMOVE_FILE
        self.id = id
        self.cname = cname
        self.root = root

    @staticmethod
    def deserialize(json_dict):
        msg = RemoveFileMessage()
        # msg.type = json_dict['type']
        # ^ I think it's assumed
        msg.id = json_dict['id']
        msg.cname = json_dict['cname']
        msg.root = json_dict['root']
        return msg

