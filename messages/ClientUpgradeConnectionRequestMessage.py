# last generated 2018-01-27 03:12:30.876000
from messages import BaseMessage
from msg_codes import CLIENT_UPGRADE_CONNECTION_REQUEST as CLIENT_UPGRADE_CONNECTION_REQUEST
__author__ = 'Mike'


class ClientUpgradeConnectionRequestMessage(BaseMessage):
    def __init__(self, upgrade_type=None, value=None):
        super(ClientUpgradeConnectionRequestMessage, self).__init__()
        self.type = CLIENT_UPGRADE_CONNECTION_REQUEST
        self.upgrade_type = upgrade_type
        self.value = value

    @staticmethod
    def deserialize(json_dict):
        msg = ClientUpgradeConnectionRequestMessage()
        msg.upgrade_type = json_dict['upgrade_type']
        msg.value = json_dict['value']
        return msg

