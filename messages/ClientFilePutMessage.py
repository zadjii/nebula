# last generated 2016-12-30 20:11:43.997000
from messages import BaseMessage
from msg_codes import CLIENT_FILE_PUT as CLIENT_FILE_PUT
__author__ = 'Mike'


class ClientFilePutMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None, fpath=None):
        super(ClientFilePutMessage, self).__init__()
        self.type = CLIENT_FILE_PUT
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = ClientFilePutMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        return msg

