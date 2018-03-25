# last generated 2018-03-24 23:21:54.181000
from messages import BaseMessage
from msg_codes import CLIENT_MAKE_DIRECTORY as CLIENT_MAKE_DIRECTORY
__author__ = 'Mike'


class ClientMakeDirectoryMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None, root=None, dir_name=None):
        super(ClientMakeDirectoryMessage, self).__init__()
        self.type = CLIENT_MAKE_DIRECTORY
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.root = root
        self.dir_name = dir_name

    @staticmethod
    def deserialize(json_dict):
        msg = ClientMakeDirectoryMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.root = json_dict['root']
        msg.dir_name = json_dict['dir_name']
        return msg

