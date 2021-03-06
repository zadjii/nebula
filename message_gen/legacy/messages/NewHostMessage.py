import json
from messages import BaseMessage
from msg_codes import NEW_HOST_MSG as NEW_HOST_MESSAGE
__author__ = 'Mike'


class NewHostMessage(BaseMessage):
    def __init__(self, port=None, wsport=None):
        super(NewHostMessage, self).__init__()
        self.type = NEW_HOST_MESSAGE
        self.port = port
        self.wsport = wsport

    @staticmethod
    def deserialize(json_dict):
        msg = NewHostMessage()
        # msg.type = json_dict['type']
        # ^ I think it's assumed
        msg.port = json_dict['port']
        msg.wsport = json_dict['wsport']
        return msg

