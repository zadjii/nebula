# last generated 2018-01-27 03:12:30.888000
from messages import BaseMessage
from msg_codes import ENABLE_ALPHA_ENCRYPTION_RESPONSE as ENABLE_ALPHA_ENCRYPTION_RESPONSE
__author__ = 'Mike'


class EnableAlphaEncryptionResponseMessage(BaseMessage):
    def __init__(self, host_public_key=None):
        super(EnableAlphaEncryptionResponseMessage, self).__init__()
        self.type = ENABLE_ALPHA_ENCRYPTION_RESPONSE
        self.host_public_key = host_public_key

    @staticmethod
    def deserialize(json_dict):
        msg = EnableAlphaEncryptionResponseMessage()
        msg.host_public_key = json_dict['host_public_key']
        return msg

