# last generated 2016-07-20 02:14:41.642000
from messages import BaseMessage
from msg_codes import CLIENT_MIRROR as CLIENT_MIRROR
__author__ = 'Mike'


class ClientMirrorMessage(BaseMessage):
    def __init__(self, sid=None, host_id=None, cloud_uname=None, cname=None):
        super(ClientMirrorMessage, self).__init__()
        self.type = CLIENT_MIRROR
        self.sid = sid
        self.host_id = host_id
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = ClientMirrorMessage()
        msg.sid = json_dict['sid']
        msg.host_id = json_dict['host_id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

