# last generated 2015-12-31 02:30:42.303000
from messages import BaseMessage
from msg_codes import HOST_HOST_FETCH as HOST_HOST_FETCH
__author__ = 'Mike'


class HostHostFetchMessage(BaseMessage):
    def __init__(self, id=None, cname=None, root=None):
        super(HostHostFetchMessage, self).__init__()
        self.type = HOST_HOST_FETCH
        self.id = id
        self.cname = cname
        self.root = root

    @staticmethod
    def deserialize(json_dict):
        msg = HostHostFetchMessage()
        msg.id = json_dict['id']
        msg.cname = json_dict['cname']
        msg.root = json_dict['root']
        return msg

