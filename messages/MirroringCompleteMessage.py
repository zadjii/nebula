# last generated 2016-12-30 20:36:48.051000
from messages import BaseMessage
from msg_codes import MIRRORING_COMPLETE as MIRRORING_COMPLETE
__author__ = 'Mike'


class MirroringCompleteMessage(BaseMessage):
    def __init__(self, id=None, cloud_uname=None, cname=None):
        super(MirroringCompleteMessage, self).__init__()
        self.type = MIRRORING_COMPLETE
        self.id = id
        self.cloud_uname = cloud_uname
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = MirroringCompleteMessage()
        msg.id = json_dict['id']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        return msg

