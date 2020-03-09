import os
import struct

from common.RelativePath import RelativePath

# from host import Cloud
# from host.PrivateData import PrivateData

__author__ = 'Mike'


def make_stat_dict(rel_path, private_data, cloud, user_id, parent_permissions=None):
    # type: (RelativePath, PrivateData, Cloud, int) -> Optional[Dict[str, Any]]
    """You should make sure file exists before calling this."""
    if rel_path is None:
        return None

    full_path = rel_path.to_absolute(cloud.root_directory)

    if not os.path.exists(full_path):
        return None

    if parent_permissions is None:
        permissions = private_data.get_permissions(user_id, rel_path)
    else:
        permissions = parent_permissions | private_data.get_permissions_no_recursion(user_id, rel_path)

    # file_path = os.path.normpath(file_path)
    file_stat = os.stat(full_path)
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
        , 'name': os.path.basename(full_path)
        , 'permissions': permissions
    }
    return stat_dict


def make_ls_array(rel_path, private_data, cloud, user_id):
    # type: (RelativePath, PrivateData, Cloud, int) -> Optional[Dict[str, Any]]
    """You should make sure file exists before calling this."""
    if rel_path is None:
        return None

    full_path = rel_path.to_absolute(cloud.root_directory)

    if not os.path.exists(full_path):
        return None

    permissions = private_data.get_permissions(user_id, rel_path)

    subdirs = []
    subfiles_list = os.listdir(full_path)
    for f in subfiles_list:
        rel_child = RelativePath()
        rel_child.from_relative(os.path.join(rel_path.to_string(), f))
        subdirs.append(make_stat_dict(rel_child, private_data, cloud, user_id, permissions))
    return subdirs


def get_msg_size(msg_json):
    size = len(msg_json)
    return struct.pack('Q', size)


def decode_msg_size(long_long):
    try:
        return struct.unpack('Q', long_long)[0]
    except Exception as e:
        print('failed to decode a size of {}'.format(long_long))
        raise e
