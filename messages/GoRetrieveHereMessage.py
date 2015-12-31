# last generated 2015-12-31 02:30:42.299000
from messages import BaseMessage
from msg_codes import GO_RETRIEVE_HERE as GO_RETRIEVE_HERE
__author__ = 'Mike'


class GoRetrieveHereMessage(BaseMessage):
    def __init__(self, id=None, ip=None, port=None):
        super(GoRetrieveHereMessage, self).__init__()
        self.type = GO_RETRIEVE_HERE
        self.id = id
        self.ip = ip
        self.port = port

    @staticmethod
    def deserialize(json_dict):
        msg = GoRetrieveHereMessage()
        msg.id = json_dict['id']
        msg.ip = json_dict['ip']
        msg.port = json_dict['port']
        return msg

