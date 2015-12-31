import os
import struct

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


def get_msg_size(msg_json):
    size = len(msg_json)
    return struct.pack('Q', size)


def decode_msg_size(long_long):
    return struct.unpack('Q', long_long)[0]