# last generated 2016-10-14 13:51:50.929000
from messages import BaseMessage
from msg_codes import ADD_OWNER_FAILURE as ADD_OWNER_FAILURE
__author__ = 'Mike'


class AddOwnerFailureMessage(BaseMessage):
    def __init__(self, message=None):
        super(AddOwnerFailureMessage, self).__init__()
        self.type = ADD_OWNER_FAILURE
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = AddOwnerFailureMessage()
        msg.message = json_dict['message']
        return msg

