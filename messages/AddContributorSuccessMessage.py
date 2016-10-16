# last generated 2016-10-14 13:51:52.142000
from messages import BaseMessage
from msg_codes import ADD_CONTRIBUTOR_SUCCESS as ADD_CONTRIBUTOR_SUCCESS
__author__ = 'Mike'


class AddContributorSuccessMessage(BaseMessage):
    def __init__(self, new_user_id=None, cloud_uname=None, cname=None):
        super(AddContributorSuccessMessage, self).__init__()
        self.type = ADD_CONTRIBUTOR_SUCCESS
        self.new_user_id = new_user_id
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = AddContributorSuccessMessage()
        msg.new_user_id = json_dict['new_user_id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

