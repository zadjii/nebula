from datetime import datetime
import os

from common_util import ResultAndData
from host import get_db, FileNode
from host.PrivateData import WRITE_ACCESS
from host.util import mylog
# from msg_codes import recv_msg
from messages import InvalidPermissionsMessage, SystemFileWriteErrorMessage
from msg_codes import CLIENT_FILE_TRANSFER

__author__ = 'Mike'


def recv_file_tree(host_obj, msg, cloud, socket_conn, db):
    rd = ResultAndData(True, None)
    while (msg.fsize is not None) and rd.success:
        is_client = msg.type == CLIENT_FILE_TRANSFER
        rd = recv_file_transfer(host_obj, msg, cloud, socket_conn, db, is_client)
        msg = socket_conn.recv_obj()


def recv_file_transfer(host_obj, msg, cloud, socket_conn, db, is_client):
    msg_file_isdir = msg.isdir
    msg_file_size = msg.fsize
    msg_rel_path = msg.fpath
    mylog('[{}] is recv\'ing <{}>'.format(cloud.my_id_from_remote, msg_rel_path))

    # if they are a client, make sure the host_obj verifies their permissions on
    # that file.
    if is_client:
        # todo: move this below getting the normpath, then re-get the relative path.
        rd = host_obj.  client_access_check_or_close(socket_conn, msg.sid, cloud,
                                                   msg_rel_path, WRITE_ACCESS)
        if not rd.success:
            return

    full_path = os.path.join(cloud.root_directory, msg_rel_path)
    full_path = os.path.normpath(full_path)
    # todo: verify that the full path is a child of clout.root_directory

    # if it' the .nebs file:
    #   If they're a client, straight up reject the change.
    #   Else, accept, and have the host reload (after reading it)
    is_private_data_file = False
    if host_obj is not None and host_obj.is_private_data_file(full_path, cloud):
        if is_client:
            err = 'Clients are not allowed to modify the {} file'.format(msg_rel_path)
            mylog(err, '33')
            response = SystemFileWriteErrorMessage(err)
            socket_conn.send_obj(response)
            return ResultAndData(False, err)
        else:
            is_private_data_file = True

    full_dir_path = os.path.dirname(full_path)
    # mylog('full_dir_path={}'.format(full_dir_path))

    # Create the path to this file, if it doesn't exist
    if not os.path.exists(full_dir_path):
        # mylog('had to make dirs for {}'.format(full_dir_path))
        os.makedirs(full_dir_path)

    if msg_file_isdir:
        if not os.path.exists(full_path):
            os.mkdir(full_path)
            # mylog('Created directory {}'.format(full_path))
    else:  # is normal file
        data_buffer = ''  # fixme i'm using a string to buffer this?? LOL
        total_read = 0
        # todo:23
        file_handle = open(full_path, mode='wb')
        file_handle.seek(0, 0)  # seek to 0B relative to start
        while total_read < msg_file_size:
            new_data = socket_conn.recv_next_data(min(1024 * 4, (msg_file_size - total_read)))
            nbytes = len(new_data)
            # print 'read ({},{})'.format(new_data, nbytes)
            if total_read is None or new_data is None:
                # todo:23 ??? what is happening here?
                print 'I know I should have broke AND I JUST DIDN\'T ANYWAYS'
                break
            total_read += nbytes
            # data_buffer += new_data
            file_handle.write(new_data)
            # print '<{}>read:{}B, total:{}B, expected total:{}B'.format(
            #     msg_rel_path, nbytes, total_read, msg_file_size
            # )
        exists = os.path.exists(full_path)

        # file_handle = None
        # try:

        # file_handle.write(data_buffer)
        file_handle.close()
        mylog('[{}] wrote the file to {}'.format(cloud.my_id_from_remote, full_path), '30;42')

    updated_node = cloud.create_or_update_node(msg_rel_path, db)
    if updated_node is not None:
        old_modified_on = updated_node.last_modified
        updated_node.last_modified = datetime.utcfromtimestamp(os.path.getmtime(full_path))
        # mylog('update mtime {}=>{}'.format(old_modified_on, updated_node.last_modified))
        db.session.commit()

    # new_num_nodes = db.session.query(FileNode).count()
    # mylog('RFT:total file nodes:{}'.format(new_num_nodes))

    if is_private_data_file:
        host_obj.reload_private_data(cloud)

    # todo:23 Send status after each transfer (FILE_TRANSFER_SUCCESS)
    return ResultAndData(True, None)


