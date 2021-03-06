# last generated 2016-08-26 15:33:31.837000
from messages import BaseMessage
from msg_codes import HOST_VERIFY_CLIENT_REQUEST as HOST_VERIFY_CLIENT_REQUEST
__author__ = 'Mike'


class HostVerifyClientRequestMessage(BaseMessage):
    def __init__(self, id=None, sid=None, cloud_uname=None, cname=None):
        super(HostVerifyClientRequestMessage, self).__init__()
        self.type = HOST_VERIFY_CLIENT_REQUEST
        self.id = id
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = HostVerifyClientRequestMessage()
        msg.id = json_dict['id']
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

