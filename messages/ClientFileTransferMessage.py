from messages import make_stat_dict
from messages.SessionMessage import SessionMessage
from msg_codes import CLIENT_FILE_TRANSFER as CLIENT_FILE_TRANSFER
__author__ = 'Mike'


class ClientFileTransferMessage(SessionMessage):
    def __init__(self, cname=None, session_id=None, fpath=None, is_dir=None, filesize=None):
        super(ClientFileTransferMessage, self).__init__(cname, session_id)
        self.type = CLIENT_FILE_TRANSFER
        self.fpath = fpath
        self.fsize = filesize
        self.isdir = is_dir

    @staticmethod
    def deserialize(json_dict):
        msg = SessionMessage.deserialize(json_dict)
        msg.fpath = json_dict['fpath']
        msg.fsize = json_dict['fsize']
        msg.isdir = json_dict['isdir']
        return msg
