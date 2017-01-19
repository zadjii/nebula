# last generated 2016-12-30 19:27:53.981000
from messages import BaseMessage
from msg_codes import REQUEST_CLOUD as REQUEST_CLOUD
__author__ = 'Mike'


class RequestCloudMessage(BaseMessage):
    def __init__(self, id=None, cloud_uname=None, cname=None, username=None, passw=None):
        super(RequestCloudMessage, self).__init__()
        self.type = REQUEST_CLOUD
        self.id = id
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.username = username
        self.passw = passw

    @staticmethod
    def deserialize(json_dict):
        msg = RequestCloudMessage()
        msg.id = json_dict['id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.username = json_dict['username']
        msg.passw = json_dict['passw']
        return msg

