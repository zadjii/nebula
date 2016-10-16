# last generated 2016-10-14 13:51:50.924000
from messages import BaseMessage
from msg_codes import ADD_CONTRIBUTOR_FAILURE as ADD_CONTRIBUTOR_FAILURE
__author__ = 'Mike'


class AddContributorFailureMessage(BaseMessage):
    def __init__(self, message=None):
        super(AddContributorFailureMessage, self).__init__()
        self.type = ADD_CONTRIBUTOR_FAILURE
        self.message = message

    @staticmethod
    def deserialize(json_dict):
        msg = AddContributorFailureMessage()
        msg.message = json_dict['message']
        return msg

