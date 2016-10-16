# last generated 2016-10-14 13:51:52.112000
from messages import BaseMessage
from msg_codes import CLIENT_ADD_OWNER as CLIENT_ADD_OWNER
__author__ = 'Mike'


class ClientAddOwnerMessage(BaseMessage):
    def __init__(self, sid=None, new_user_id=None, cloud_uname=None, cname=None):
        super(ClientAddOwnerMessage, self).__init__()
        self.type = CLIENT_ADD_OWNER
        self.sid = sid
        self.new_user_id = new_user_id
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = ClientAddOwnerMessage()
        msg.sid = json_dict['sid']
        msg.new_user_id = json_dict['new_user_id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

