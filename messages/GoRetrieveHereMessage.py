# last generated 2017-02-24 16:24:07.551000
from messages import BaseMessage
from msg_codes import GO_RETRIEVE_HERE as GO_RETRIEVE_HERE
__author__ = 'Mike'


class GoRetrieveHereMessage(BaseMessage):
    def __init__(self, id=None, ip=None, port=None, owner_ids=None, max_size=None):
        super(GoRetrieveHereMessage, self).__init__()
        self.type = GO_RETRIEVE_HERE
        self.id = id
        self.ip = ip
        self.port = port
        self.owner_ids = owner_ids
        self.max_size = max_size

    @staticmethod
    def deserialize(json_dict):
        msg = GoRetrieveHereMessage()
        msg.id = json_dict['id']
        msg.ip = json_dict['ip']
        msg.port = json_dict['port']
        msg.owner_ids = json_dict['owner_ids']
        msg.max_size = json_dict['max_size']
        return msg

