# last generated 2018-04-08 02:13:50.667000
from messages import BaseMessage
from msg_codes import CLIENT_CREATE_LINK_REQUEST as CLIENT_CREATE_LINK_REQUEST
__author__ = 'Mike'


class ClientCreateLinkRequestMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None, path=None):
        super(ClientCreateLinkRequestMessage, self).__init__()
        self.type = CLIENT_CREATE_LINK_REQUEST
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.path = path

    @staticmethod
    def deserialize(json_dict):
        msg = ClientCreateLinkRequestMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.path = json_dict['path']
        return msg

