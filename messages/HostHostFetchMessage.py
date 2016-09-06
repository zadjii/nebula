# last generated 2016-09-05 22:58:36.385000
from messages import BaseMessage
from msg_codes import HOST_HOST_FETCH as HOST_HOST_FETCH
__author__ = 'Mike'


class HostHostFetchMessage(BaseMessage):
    def __init__(self, my_id=None, other_id=None, cloud_uname=None, cname=None, root=None):
        super(HostHostFetchMessage, self).__init__()
        self.type = HOST_HOST_FETCH
        self.my_id = my_id
        self.other_id = other_id
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.root = root

    @staticmethod
    def deserialize(json_dict):
        msg = HostHostFetchMessage()
        msg.my_id = json_dict['my_id']
        msg.other_id = json_dict['other_id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.root = json_dict['root']
        return msg

