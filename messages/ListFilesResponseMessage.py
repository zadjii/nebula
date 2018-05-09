# last generated 2015-12-31 02:30:42.338000
from messages import BaseMessage
from msg_codes import LIST_FILES_RESPONSE as LIST_FILES_RESPONSE
from messages.util import *
__author__ = 'Mike'


class ListFilesResponseMessage(BaseMessage):
    def __init__(self, sid=None, cname=None, fpath=None):
        super(ListFilesResponseMessage, self).__init__()
        self.type = LIST_FILES_RESPONSE
        self.sid = sid
        self.cname = cname
        self.fpath = fpath
        # Note: You need to instantiate these members using the cloud and the
        #   PrivateData for that cloud
        # self.stat = make_stat_dict(fpath)
        # self.ls = make_ls_array(fpath)
        self.stat = None
        self.ls = None

    @staticmethod
    def deserialize(json_dict):
        msg = ListFilesResponseMessage()
        msg.sid = json_dict['sid']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        msg.ls = json_dict['ls']
        msg.stat = json_dict['stat']
        return msg

