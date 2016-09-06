# last generated 2016-09-05 19:18:54.186000
from messages import BaseMessage
from msg_codes import HOST_VERIFY_HOST_SUCCESS as HOST_VERIFY_HOST_SUCCESS
__author__ = 'Mike'


class HostVerifyHostSuccessMessage(BaseMessage):
    def __init__(self, my_id=None, their_id=None, cloud_uname=None, cname=None):
        super(HostVerifyHostSuccessMessage, self).__init__()
        self.type = HOST_VERIFY_HOST_SUCCESS
        self.my_id = my_id
        self.their_id = their_id
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = HostVerifyHostSuccessMessage()
        msg.my_id = json_dict['my_id']
        msg.their_id = json_dict['their_id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

