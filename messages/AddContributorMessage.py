# last generated 2016-10-14 13:51:52.136000
from messages import BaseMessage
from msg_codes import ADD_CONTRIBUTOR as ADD_CONTRIBUTOR
__author__ = 'Mike'


class AddContributorMessage(BaseMessage):
    def __init__(self, host_id=None, new_user_id=None, cloud_uname=None, cname=None):
        super(AddContributorMessage, self).__init__()
        self.type = ADD_CONTRIBUTOR
        self.host_id = host_id
        self.new_user_id = new_user_id
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = AddContributorMessage()
        msg.host_id = json_dict['host_id']
        msg.new_user_id = json_dict['new_user_id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

