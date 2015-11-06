import os
from messages.BaseMessage import BaseMessage
from messages.NewHostMessage import NewHostMessage
from messages.AssignHostIDMessage import AssignHostIDMessage
from messages.HostHandshakeMessage import HostHandshakeMessage
# from messages.RemoteHandshakeMessage import RemoteHandshakeMessage  # unused?
# from messages.RemoteHandshakeGoFetchMessage import RemoteHandshakeGoFetchMessage  # unused?
from messages.RequestCloudMessage import RequestCloudMessage
from messages.GoRetrieveMessage import GoRetrieveMessage
from messages.PrepareForFetchMessage import PrepareForFetchMessage
from messages.HostHostFetchMessage import HostHostFetchMessage
from messages.HostFileTransferMessage import HostFileTransferMessage
# from messages.MakeCloudRequestMessage import MakeCloudRequestMessage  # todo
# from messages.MakeCloudResponseMessage import MakeCloudResponseMessage  # todo
# from messages.MakeUserRequestMessage import MakeUserRequestMessage  # todo
# from messages.MakeUserResponseMessage import MakeUserResponseMessage  # todo
from messages.MirroringCompleteMessage import MirroringCompleteMessage
from messages.GetHostsRequestMessage import GetHostsRequestMessage
from messages.GetHostsResponseMessage import GetHostsResponseMessage
from messages.RemoveFileMessage import RemoveFileMessage
from messages.HostFilePushMessage import HostFilePushMessage
from messages.StatFileRequestMessage import StatFileRequestMessage
from messages.StatFileResponseMessage import StatFileResponseMessage
from messages.ListFilesRequestMessage import ListFilesRequestMessage
from messages.ListFilesResponseMessage import ListFilesResponseMessage
# from messages.ReadFileRequestMessage import ReadFileRequestMessage # todo
# from messages.ReadFileResponseMessage import ReadFileResponseMessage # todo
from messages.ClientSessionRequestMessage import ClientSessionRequestMessage
from messages.ClientSessionAlertMessage import ClientSessionAlertMessage
from messages.ClientSessionResponseMessage import ClientSessionResponseMessage
from messages.ClientFilePutMessage import ClientFilePutMessage
from messages.ClientFileTransferMessage import ClientFileTransferMessage

__author__ = 'Mike'


def make_stat_dict(file_path):
    """You should make sure file exists before calling this."""
    if file_path is None:
        return None
    if not os.path.exists(file_path):
        return None
    file_path = os.path.normpath(file_path)
    file_stat = os.stat(file_path)
    stat_dict = {
        'atime': file_stat.st_atime
        , 'mtime': file_stat.st_mtime
        , 'ctime': file_stat.st_ctime
        , 'inode': file_stat.st_ino
        , 'mode': file_stat.st_mode
        , 'dev': file_stat.st_dev
        , 'nlink': file_stat.st_nlink
        , 'uid': file_stat.st_uid
        , 'gid': file_stat.st_gid
        , 'size': file_stat.st_size
        , 'name': os.path.basename(file_path)
    }
    return stat_dict


def make_ls_array(file_path):
    """You should make sure file exists before calling this."""
    if file_path is None:
        return None
    if not os.path.exists(file_path):
        return None
    file_path = os.path.normpath(file_path)
    subdirs = []
    if not os.path.isdir(file_path):
        # fixme this should somehow indicate the path was not a dir
        # cont not just that it had no children
        return subdirs
    subfiles_list = os.listdir(file_path)
    # print subfiles_list
    for f in subfiles_list:
        subdirs.append(make_stat_dict(os.path.join(file_path, f)))
    return subdirs


