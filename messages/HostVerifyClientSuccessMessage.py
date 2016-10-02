# last generated 2016-10-01 23:26:42.129000
from messages import BaseMessage
from msg_codes import HOST_VERIFY_CLIENT_SUCCESS as HOST_VERIFY_CLIENT_SUCCESS
__author__ = 'Mike'


class HostVerifyClientSuccessMessage(BaseMessage):
    def __init__(self, id=None, sid=None, cloud_uname=None, cname=None, user_id=None):
        super(HostVerifyClientSuccessMessage, self).__init__()
        self.type = HOST_VERIFY_CLIENT_SUCCESS
        self.id = id
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.user_id = user_id

    @staticmethod
    def deserialize(json_dict):
        msg = HostVerifyClientSuccessMessage()
        msg.id = json_dict['id']
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.user_id = json_dict['user_id']
        return msg

