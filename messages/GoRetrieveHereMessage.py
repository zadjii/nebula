# last generated 2017-02-24 16:24:07.551000
from messages import BaseMessage
from msg_codes import GO_RETRIEVE_HERE as GO_RETRIEVE_HERE
__author__ = 'Mike'


class GoRetrieveHereMessage(BaseMessage):
    def __init__(self, requester_id=None, other_id=None, ip=None, port=None, owner_ids=None, max_size=None):
        super(GoRetrieveHereMessage, self).__init__()
        self.type = GO_RETRIEVE_HERE
        self.requester_id = requester_id
        self.other_id = other_id
        self.ip = ip
        self.port = port
        self.owner_ids = owner_ids
        self.max_size = max_size

    @staticmethod
    def deserialize(json_dict):
        msg = GoRetrieveHereMessage()
        msg.requester_id = json_dict['requester_id']
        msg.other_id = json_dict['other_id']
        msg.ip = json_dict['ip']
        msg.port = json_dict['port']
        msg.owner_ids = json_dict['owner_ids']
        msg.max_size = json_dict['max_size']
        return msg

# Okay you're gonna make setup_remote_socket a method on "remote"'
# pass the Remote model into request_cloud
# RequestCloudMessage needs to send the Remote.my_id_from_remote, not the cloud one.
# GoRetrieveHere responds with the new Mirror.id, so that the finish_request_cloud can put that value into the host.models.Cloud object.
