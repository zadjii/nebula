import json
__author__ = 'Mike'


class BaseMessage(object):
    def __init__(self):
        self.type = None

    def serialize(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def deserialize(json_dict):
        msg = BaseMessage()
        msg.type = json_dict['type']
        return msg
