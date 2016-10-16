# last generated 2016-10-14 13:51:52.116000
from messages import BaseMessage
from msg_codes import ADD_OWNER_SUCCESS as ADD_OWNER_SUCCESS
__author__ = 'Mike'


class AddOwnerSuccessMessage(BaseMessage):
    def __init__(self, sid=None, new_user_id=None, cloud_uname=None, cname=None):
        super(AddOwnerSuccessMessage, self).__init__()
        self.type = ADD_OWNER_SUCCESS
        self.sid = sid
        self.new_user_id = new_user_id
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = AddOwnerSuccessMessage()
        msg.sid = json_dict['sid']
        msg.new_user_id = json_dict['new_user_id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

