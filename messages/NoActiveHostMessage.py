# last generated 2016-08-30 02:47:27.053000
from messages import BaseMessage
from msg_codes import NO_ACTIVE_HOST as NO_ACTIVE_HOST
__author__ = 'Mike'


class NoActiveHostMessage(BaseMessage):
    def __init__(self, cloud_uname=None, cname=None):
        super(NoActiveHostMessage, self).__init__()
        self.type = NO_ACTIVE_HOST
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = NoActiveHostMessage()
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

