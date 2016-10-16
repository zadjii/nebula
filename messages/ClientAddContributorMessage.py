# last generated 2016-10-14 13:51:52.131000
from messages import BaseMessage
from msg_codes import CLIENT_ADD_CONTRIBUTOR as CLIENT_ADD_CONTRIBUTOR
__author__ = 'Mike'


class ClientAddContributorMessage(BaseMessage):
    def __init__(self, sid=None, new_user_id=None, cloud_uname=None, cname=None, fpath=None, permissions=None):
        super(ClientAddContributorMessage, self).__init__()
        self.type = CLIENT_ADD_CONTRIBUTOR
        self.sid = sid
        self.new_user_id = new_user_id
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.fpath = fpath
        self.permissions = permissions

    @staticmethod
    def deserialize(json_dict):
        msg = ClientAddContributorMessage()
        msg.sid = json_dict['sid']
        msg.new_user_id = json_dict['new_user_id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        msg.permissions = json_dict['permissions']
        return msg

