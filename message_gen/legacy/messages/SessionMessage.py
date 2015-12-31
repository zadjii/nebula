__author__ = 'Mike'
from messages import BaseMessage


class SessionMessage(BaseMessage):
    def __init__(self, session_id=None):
        super(SessionMessage, self).__init__()
        # self.cname = cname
        self.sid = session_id

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage()
        msg.type = json_dict['type']
        # msg.cname = json_dict['cname']
        msg.sid = json_dict['sid']
        return msg


