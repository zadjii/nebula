# last generated 2015-12-31 02:30:42.283000
from messages import BaseMessage
from msg_codes import NEW_HOST as NEW_HOST
__author__ = 'Mike'


class NewHostMessage(BaseMessage):
    def __init__(self, port=None, wsport=None):
        super(NewHostMessage, self).__init__()
        self.type = NEW_HOST
        self.port = port
        self.wsport = wsport

    @staticmethod
    def deserialize(json_dict):
        msg = NewHostMessage()
        msg.port = json_dict['port']
        msg.wsport = json_dict['wsport']
        return msg

