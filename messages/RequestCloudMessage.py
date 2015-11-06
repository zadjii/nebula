import json
from messages import BaseMessage
from msg_codes import REQUEST_CLOUD as REQUEST_CLOUD
__author__ = 'Mike'


class RequestCloudMessage(BaseMessage):
    def __init__(self, id=None, cname=None, uname=None, passw=None):
        super(RequestCloudMessage, self).__init__()
        self.type = REQUEST_CLOUD
        self.id = id
        self.cname = cname
        self.uname = uname
        self.passw = passw

    @staticmethod
    def deserialize(json_dict):
        msg = RequestCloudMessage()
        # msg.type = json_dict['type']
        # ^ I think it's assumed
        msg.id = json_dict['id']
        msg.cname = json_dict['cname']
        msg.uname = json_dict['uname']
        msg.passw = json_dict['passw']
        return msg

