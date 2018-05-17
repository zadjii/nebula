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
    # msg_file_isdir = msg.isdir
    # msg_file_size = msg.fsize
    # msg_rel_path = msg.fpath
    # mylog('[{}] is recv\'ing <{}>'.format(cloud.my_id_from_remote, msg_rel_path))

    # rel_path = RelativePath()
    # def _clog(result):
    #     if is_client:
    #         host_obj.log_client_sid(msg.sid, 'write', cloud, rel_path, result)

    # rd = rel_path.from_relative(msg_rel_path)
    # if not rd.success:
    #     msg = '{} is not a valid cloud path'.format(msg_rel_path)
    #     err = InvalidStateMessage(msg)
    #     _log.debug(err)
    #     send_error_and_close(err, socket_conn)
    #     _clog('error')
    #     return rd

    # # if they are a client, make sure the host_obj verifies their permissions on
    # # that file.
    # if is_client:
    #     # TODO#27: check if the parent has append on the parent.
    #     # if the parent has APPEND permissions, then we can add a new child
    #     # If we do add a new child, then we should make that child writable by
    #     #   the user who's writing it currently.
    #     # If the user only has append permissions, and the file already exists,
    #     # we have to reject that.
    #     rd = host_obj.client_access_check_or_close(socket_conn, msg.sid, cloud,
    #                                                rel_path, WRITE_ACCESS)
    #     if not rd.success:
    #         _clog('error')
    #         return rd

    full_path = rel_path.to_absolute(cloud.root_directory)

    # if it' the .nebs file:
    #   If they're a client, straight up reject the change.
    #   Else, accept, and have the host reload (after reading it)
    is_private_data_file = False
    # if host_obj is not None and host_obj.is_private_data_file(full_path, cloud):
    #     if is_client:
    #         err = 'Clients are not allowed to modify the {} file'.format(msg_rel_path)
    #         mylog(err, '33')
    #         response = SystemFileWriteErrorMessage(err)
    #         socket_conn.send_obj(response)
    #         _clog('error')
    #         return ResultAndData(False, err)
    #     else:
    #         is_private_data_file = True

    if host_obj.is_private_data_file(full_path, cloud):
        is_private_data_file = True

    full_dir_path = os.path.dirname(full_path)
    mylog('full_dir_path={}'.format(full_dir_path))

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
                # _log.debug(err)
                # socket_conn.send_obj(resp)
                # _clog('error')
                # return ResultAndData(False, err)
            else:
                err = 'Path {} already exists'.format(full_dir_path)
                resp = FileAlreadyExistsMessage(full_dir_path)
                return Error(resp)
                # _log.debug(err)
                # socket_conn.send_obj(resp)
                # _clog('error')
                # return ResultAndData(False, err)

    if not os.path.isdir(full_dir_path):
        err = '{} is not a directory'.format(full_dir_path)
        resp = FileIsNotDirErrorMessage()
        return Error(resp)
        # _log.debug(err)
        # socket_conn.send_obj(resp)
        # _clog('error')
        # return ResultAndData(False, err)

    if is_dir:
        if not os.path.exists(full_path):
            try:
                os.mkdir(full_path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    err = 'I/O Error creating path {}'.format(full_dir_path)
                    resp = UnknownIoErrorMessage(err)
                    return Error(resp)
                    # _log.debug(err)
                    # socket_conn.send_obj(resp)
                    # _clog('error')
                    # return ResultAndData(False, err)
                else:
                    err = 'Path {} already exists'.format(full_dir_path)
                    resp = FileAlreadyExistsMessage(full_dir_path)
                    return Error(resp)
                    # _log.debug(err)
                    # socket_conn.send_obj(resp)
                    # _clog('error')
                    # return ResultAndData(False, err)

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
            # _log.debug(err)
            # socket_conn.send_obj(resp)
            # _clog('error')
            # return Error(err)
        # _log.debug('[{}] wrote the file to {}'.format(cloud.my_id_from_remote, full_path), '30;42')

    # _clog('success')
    resp = FileTransferSuccessMessage(cloud.uname(), cloud.cname(), rel_path.to_string())
    # socket_conn.send_obj(resp)

    # # if it wasn't a client file transfer, update our node.
    # #   We don't want to see that it was updated and send updates to the other hosts.
    # # else (this came from a client):
    # #   We DO want to tell other mirrors about this change, so don't change the DB>
    # #   The local thread will find the change and alert the other mirrors.
    # if not is_client:
    #     updated_node = cloud.create_or_update_node(rel_path.to_string(), db)
    #     if updated_node is not None:
    #         old_modified_on = updated_node.last_modified
    #         updated_node.last_modified = datetime.utcfromtimestamp(os.path.getmtime(full_path))
    #         # mylog('update mtime {}=>{}'.format(old_modified_on, updated_node.last_modified))
    #         db.session.commit()

    # new_num_nodes = db.session.query(FileNode).count()
    # mylog('RFT:total file nodes:{}'.format(new_num_nodes))

    if is_private_data_file:
        host_obj.reload_private_data(cloud)

    return Success(resp)


