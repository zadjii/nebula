# last generated 2015-12-31 02:30:42.294000
from messages import BaseMessage
from msg_codes import REM_HANDSHAKE_GO_FETCH as REM_HANDSHAKE_GO_FETCH
__author__ = 'Mike'


class RemHandshakeGoFetchMessage(BaseMessage):
    def __init__(self):
        super(RemHandshakeGoFetchMessage, self).__init__()
        self.type = REM_HANDSHAKE_GO_FETCH

    @staticmethod
    def deserialize(json_dict):
        msg = RemHandshakeGoFetchMessage()
        return msg

