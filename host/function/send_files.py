import os
import shutil
from stat import S_ISDIR

from datetime import datetime

from common_util import Error, Success, ResultAndData, datetime_to_string, get_mylog
from common.RelativePath import RelativePath
from host.util import mylog
from host import Cloud
from messages import HostFileTransferMessage

__author__ = 'Mike'


def send_tree(db, other_id, cloud, rel_path, connection):
    # type: (SimpleDB, int, Cloud, RelativePath, AbstractConnection) -> None
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
    _log = get_mylog()
    # mylog('They requested the file {}'.format(requested_root))
    # # find the file on the system, get it's size.
    # requesting_all = requested_root == '/'
    # filepath = None
    # # if the root is '/', send all of the children of the root
    # if requesting_all:
    #     filepath = cloud.root_directory
    # else:
    #     filepath = os.path.join(cloud.root_directory, requested_root)
    # mylog('The translated request path was {}'.format(rel_path.to_absolute(cloud.root_directory)))

    matching_local_mirror = db.session.query(Cloud).filter_by(my_id_from_remote=other_id).first()
    is_local = matching_local_mirror is not None
    if is_local:
        _log.debug('Sending file tree to local')
        send_file_to_local(db, cloud, matching_local_mirror, rel_path, True)
    else:
        _log.debug('Sending file tree to other')
        send_file_to_other(other_id, cloud, rel_path, connection)
    complete_sending_files(other_id, cloud, rel_path, connection)
    connection.close()


def send_file_to_local(db, src_mirror, tgt_mirror, relative_pathname, recurse=False):
    # type: (SimpleDB, Cloud, Cloud, RelativePath) -> ResultAndData
    rd = Error()
    full_src_path = relative_pathname.to_absolute(src_mirror.root_directory)
    full_tgt_path = relative_pathname.to_absolute(tgt_mirror.root_directory)

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
        updated_node = tgt_mirror.make_tree(relative_pathname, db)
        if updated_node is not None:
            old_modified_on = updated_node.last_modified
            updated_node.last_modified = datetime.utcfromtimestamp(os.path.getmtime(full_tgt_path))
            mylog('update mtime {}=>{}'.format(old_modified_on, updated_node.last_modified))

            src_node = src_mirror.get_child_node(relative_pathname)
            last_sync = src_node.last_sync() if src_node.is_root() else src_node.last_sync
            if not updated_node.is_root():
                updated_node.last_sync = last_sync

            db.session.commit()
        else:
            mylog('ERROR: Failed to create a FileNode for the new file {}'.format(full_tgt_path))


    if src_file_is_dir and recurse:
        subdirectories = os.listdir(full_src_path)
        # mylog('Sending children of <{}>={}'.format(filepath, subdirectories))
        for f in subdirectories:
            child_rel_path = RelativePath()
            child_rel_path.from_relative(os.path.join(relative_pathname.to_string(), f))
            send_file_to_local(db, src_mirror, tgt_mirror, child_rel_path, recurse)

    return rd


def send_file_to_other(other_id, cloud, rel_path, socket_conn, recurse=True):
    # type: (int, Cloud, RelativePath, AbstractConnection, bool) -> None
    """
    Assumes that the other host was already verified, and the cloud is non-null
    """
    _log = get_mylog()
    full_path = rel_path.to_absolute(cloud.root_directory)
    req_file_stat = os.stat(full_path)
    # relative_pathname = os.path.relpath(filepath, cloud.root_directory)
    # print 'relpath({}) in \'{}\' is <{}>'.format(filepath, cloud.name, relative_pathname)

    req_file_is_dir = S_ISDIR(req_file_stat.st_mode)

    uname = cloud.uname()
    cname = cloud.cname()
    rel_path_string = rel_path.to_string()
    node = cloud.get_child_node(rel_path)
    last_sync = None
    if node is not None:
        last_sync = datetime_to_string(node.last_sync()) if node.is_root() else datetime_to_string(node.last_sync)
    _log.debug('"{}"\'s last_sync was {}'.format(rel_path.to_string(), last_sync))
    # mylog('filepath<{}> is_dir={}'.format(filepath, req_file_is_dir))
    if req_file_is_dir:
        if not rel_path.is_root():
            _log.debug('Sending directory')
            msg = HostFileTransferMessage(other_id, uname, cname, rel_path_string, 0, req_file_is_dir, last_sync)
            socket_conn.send_obj(msg)
            _log.debug('Sent msg={}'.format(msg))
            # TODO#23: The other host should reply with FileTransferSuccessMessage

        if recurse:
            subdirectories = os.listdir(full_path)
            # mylog('Sending children of <{}>={}'.format(filepath, subdirectories))
            for f in subdirectories:
                child_rel_path = RelativePath()
                child_rel_path.from_relative(os.path.join(rel_path_string, f))
                send_file_to_other(other_id, cloud, child_rel_path, socket_conn)

    else:
        _log.debug('Sending file')
        req_file_size = req_file_stat.st_size
        requested_file = open(full_path, 'rb')
        _log.debug('file size is {}'.format(req_file_size))
        msg = HostFileTransferMessage(other_id, uname, cname, rel_path_string, req_file_size, req_file_is_dir, last_sync)
        socket_conn.send_obj(msg)
        _log.debug('Sent msg={}'.format(msg.serialize()))
        l = 1
        while l:
            new_data = requested_file.read(1024)
            l = socket_conn.send_next_data(new_data)
            _log.debug('Sent data="{}"'.format(new_data))
            # mylog(
            #     '[{}]Sent {}B of file<{}> data'
            #     .format(cloud.my_id_from_remote, l, filepath)
            # )
        # mylog(
        #     '[{}]Sent <{}> data to [{}]'
        #     .format(cloud.my_id_from_remote, full_path, other_id)
        # )

        requested_file.close()


def complete_sending_files(other_id, cloud, filepath, socket_conn):

    msg = HostFileTransferMessage(other_id, cloud.uname(), cloud.cname(), None, None, None)
    socket_conn.send_obj(msg)
    mylog('[{}] completed sending files to [{}]'
          .format(cloud.my_id_from_remote, other_id))


