# last generated 2015-12-31 02:30:42.318000
from messages import BaseMessage
from msg_codes import MIRRORING_COMPLETE as MIRRORING_COMPLETE
__author__ = 'Mike'


class MirroringCompleteMessage(BaseMessage):
    def __init__(self, id=None, cname=None):
        super(MirroringCompleteMessage, self).__init__()
        self.type = MIRRORING_COMPLETE
        self.id = id
        self.cname = cname

    @staticmethod
    def deserialize(json_dict):
        msg = MirroringCompleteMessage()
        msg.id = json_dict['id']
        msg.cname = json_dict['cname']
        return msg

