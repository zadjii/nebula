import os
import shutil
from stat import S_ISDIR

from datetime import datetime

from common_util import Error, Success
from host.util import mylog
from messages import HostFileTransferMessage

__author__ = 'Mike'


def send_tree(db, other_id, cloud, requested_root, connection):
    """
    Note: This can't be used to send a tree of files over the network
    to a mirror on the same host process. It blocks and is bad.
    Fortunately, this is only used by `nebs mirror` at the momment,
    so we don't need to worry.
    :param db:
    :param other_id:
    :param cloud:
    :param requested_root:
    :param connection:
    :return:
    """
    mylog('They requested the file {}'.format(requested_root))
    # find the file on the system, get it's size.
    requesting_all = requested_root == '/'
    filepath = None
    # if the root is '/', send all of the children of the root
    if requesting_all:
        filepath = cloud.root_directory
    else:
        filepath = os.path.join(cloud.root_directory, requested_root)
    mylog('The translated request path was {}'.format(filepath))

    send_file_to_other(other_id, cloud, filepath, connection)
    complete_sending_files(other_id, cloud, filepath, connection)
    connection.close()


def send_file_to_local(db, src_mirror, tgt_mirror, relative_pathname):
    # type: (SimpleDB, Cloud, Cloud, str) -> ResultAndData
    rd = Error()
    full_src_path = os.path.join(src_mirror.root_directory, relative_pathname)
    full_tgt_path = os.path.join(tgt_mirror.root_directory, relative_pathname)

    src_file_stat = os.stat(full_src_path)
    src_file_is_dir = S_ISDIR(src_file_stat.st_mode)

    rd = Success()
    try:
        if src_file_is_dir and not os.path.exists(full_tgt_path):
            os.mkdir(full_tgt_path)
        else:
            shutil.copy2(full_src_path, full_tgt_path)
    except IOError as e:
        rd = Error(e)

    if rd.success:
        updated_node = tgt_mirror.create_or_update_node(relative_pathname, db)
        if updated_node is not None:
            old_modified_on = updated_node.last_modified
            updated_node.last_modified = datetime.utcfromtimestamp(os.path.getmtime(full_tgt_path))
            # mylog('update mtime {}=>{}'.format(old_modified_on, updated_node.last_modified))
            db.session.commit()
        else:
            mylog('ERROR: Failed to create a FileNode for the new file {}'.format(full_tgt_path))

    return rd


def send_file_to_other(other_id, cloud, filepath, socket_conn, recurse=True):
    """
    Assumes that the other host was already verified, and the cloud is non-null
    """
    req_file_stat = os.stat(filepath)
    relative_pathname = os.path.relpath(filepath, cloud.root_directory)
    # print 'relpath({}) in \'{}\' is <{}>'.format(filepath, cloud.name, relative_pathname)

    req_file_is_dir = S_ISDIR(req_file_stat.st_mode)
    mylog('filepath<{}> is_dir={}'.format(filepath, req_file_is_dir))
    if req_file_is_dir:
        if relative_pathname != '.':
            msg = HostFileTransferMessage(
                other_id
                , cloud.uname()
                , cloud.cname()
                , relative_pathname
                , 0
                , req_file_is_dir
            )
            socket_conn.send_obj(msg)

        if recurse:
            subdirectories = os.listdir(filepath)
            mylog('Sending children of <{}>={}'.format(filepath, subdirectories))
            for f in subdirectories:
                send_file_to_other(other_id, cloud, os.path.join(filepath, f), socket_conn)
    else:
        req_file_size = req_file_stat.st_size
        requested_file = open(filepath, 'rb')
        msg = HostFileTransferMessage(
            other_id
            , cloud.uname()
            , cloud.cname()
            , relative_pathname
            , req_file_size
            , req_file_is_dir
        )
        socket_conn.send_obj(msg)

        l = 1
        while l:
            new_data = requested_file.read(1024)
            l = socket_conn.send_next_data(new_data)
            mylog(
                '[{}]Sent {}B of file<{}> data'
                .format(cloud.my_id_from_remote, l, filepath)
            )
        mylog(
            '[{}]Sent <{}> data to [{}]'
            .format(cloud.my_id_from_remote, filepath, other_id)
        )

        requested_file.close()


def complete_sending_files(other_id, cloud, filepath, socket_conn):

    msg = HostFileTransferMessage(other_id, cloud.uname(), cloud.cname(), None, None, None)
    socket_conn.send_obj(msg)
    mylog('[{}] completed sending files to [{}]'
          .format(cloud.my_id_from_remote, other_id))


