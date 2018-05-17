from datetime import datetime
import os

import errno

from common_util import ResultAndData, RelativePath, get_mylog, send_error_and_close, Error, Success
from host.PrivateData import WRITE_ACCESS
from host.models import Cloud
from host.util import mylog, get_client_session
# from msg_codes import recv_msg
from messages import *
from msg_codes import CLIENT_FILE_TRANSFER

__author__ = 'Mike'


def recv_file_tree(host_obj, msg, cloud, socket_conn, db):
    rd = ResultAndData(True, None)
    while (msg.fsize is not None) and rd.success:
        is_client = msg.type == CLIENT_FILE_TRANSFER
        rd = recv_file_transfer(host_obj, msg, cloud, socket_conn, db, is_client)
        msg = socket_conn.recv_obj()


def recv_file_transfer(host_obj, msg, cloud, socket_conn, db, is_client):
    # type: (HostController, BaseMessage, Cloud, AbstractConnection, SimpleDB, bool) -> ResultAndData
    _log = get_mylog()
    msg_file_isdir = msg.isdir
    msg_file_size = msg.fsize
    msg_rel_path = msg.fpath
    rel_path = RelativePath()
    rd = rel_path.from_relative(msg_rel_path)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(msg_rel_path)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        send_error_and_close(err, socket_conn)
        return rd

    full_path = rel_path.to_absolute(cloud.root_directory)
    rd = do_recv_file_transfer(host_obj, cloud, socket_conn, rel_path, msg_file_isdir, msg_file_size)
    if rd.success:

        # if it wasn't a client file transfer, update our node.
        #   We don't want to see that it was updated and send updates to the other hosts.
        # else (this came from a client):
        #   We DO want to tell other mirrors about this change, so don't change the DB>
        #   The local thread will find the change and alert the other mirrors.
        # if not is_client:
        updated_node = cloud.create_or_update_node(rel_path.to_string(), db)
        if updated_node is not None:
            old_modified_on = updated_node.last_modified
            updated_node.last_modified = datetime.utcfromtimestamp(os.path.getmtime(full_path))
            # mylog('update mtime {}=>{}'.format(old_modified_on, updated_node.last_modified))
            db.session.commit()


def do_recv_file_transfer(host_obj, cloud, socket_conn, rel_path, is_dir, fsize):
    # type: (HostController, Cloud, AbstractConnection, RelativePath, bool, int) -> ResultAndData
    _log = get_mylog()
    if host_obj is None:
        return Error(InvalidStateMessage('Did not supply a host_obj to do_recv_file_transfer'))

    full_path = rel_path.to_absolute(cloud.root_directory)

    is_private_data_file = host_obj.is_private_data_file(full_path, cloud)

    full_dir_path = os.path.dirname(full_path)
    _log.debug('full_dir_path={}'.format(full_dir_path))

    # Create the path to this file, if it doesn't exist
    if not os.path.exists(full_dir_path):
        _log.debug('had to make dirs for {}'.format(full_dir_path))
        try:
            os.makedirs(full_dir_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                err = 'I/O Error creating path {}'.format(full_dir_path)
                resp = UnknownIoErrorMessage(err)
                return Error(resp)
            else:
                err = 'Path {} already exists'.format(full_dir_path)
                resp = FileAlreadyExistsMessage(full_dir_path)
                return Error(resp)

    if not os.path.isdir(full_dir_path):
        err = '{} is not a directory'.format(full_dir_path)
        resp = FileIsNotDirErrorMessage()
        return Error(resp)

    if is_dir:
        if not os.path.exists(full_path):
            try:
                os.mkdir(full_path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    err = 'I/O Error creating path {}'.format(full_dir_path)
                    resp = UnknownIoErrorMessage(err)
                    return Error(resp)
                else:
                    err = 'Path {} already exists'.format(full_dir_path)
                    resp = FileAlreadyExistsMessage(full_dir_path)
                    return Error(resp)

    else:  # is normal file
        data_buffer = ''  # fixme i'm using a string to buffer this?? LOL
        total_read = 0
        while total_read < fsize:
            new_data = socket_conn.recv_next_data(min(1024, (fsize - total_read)))
            nbytes = len(new_data)
            if total_read is None or new_data is None:
                # todo:23 ??? what is happening here?
                print 'I know I should have broke AND I JUST DIDN\'T ANYWAYS'
                break
            total_read += nbytes
            data_buffer += new_data

        # exists = os.path.exists(full_path)
        # file_handle = None
        try:
            file_handle = open(full_path, mode='wb')
            file_handle.seek(0, 0)  # seek to 0B relative to start
            file_handle.write(data_buffer)
            file_handle.close()
        except (OSError, IOError) as e:
            err = 'I/O Error writing file path {} - ERRNO:{}'.format(rel_path.to_string(), e.errno)
            resp = UnknownIoErrorMessage(err)
            return Error(resp)

    resp = FileTransferSuccessMessage(cloud.uname(), cloud.cname(), rel_path.to_string())

    if is_private_data_file:
        host_obj.reload_private_data(cloud)

    return Success(resp)


