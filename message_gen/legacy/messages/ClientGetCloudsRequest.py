from messages.SessionMessage import SessionMessage
from msg_codes import CLIENT_GET_CLOUDS_REQUEST as CLIENT_GET_CLOUDS_REQUEST
__author__ = 'Mike'


class ClientGetCloudsRequest(SessionMessage):
    def __init__(self, session_id=None):
        super(ClientGetCloudsRequest, self).__init__(session_id)
        self.type = CLIENT_GET_CLOUDS_REQUEST
        # self.fpath = fpath
        # self.ls = make_ls_array(fpath)

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        # msg.fpath = json_dict['fpath']
        # msg.ls = json_dict['ls']
        return msg
