import math
import os
import time
from stat import S_ISDIR

from common_util import mylog, send_error_and_close, Success, Error
from host import get_db, Cloud
from host.PrivateData import READ_ACCESS, SHARE_ACCESS
from host.function.recv_files import recv_file_tree
from host.util import check_response, validate_or_get_client_session, \
    permissions_are_sufficient
from messages import *
from msg_codes import *


def handle_recv_file_from_client(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj
                                  , do_recv_file_from_client)


def do_recv_file_from_client(host_obj, connection, address, msg_obj, client):
    db = get_db()
    cloud = client.cloud
    cloudname = cloud.name
    # todo: maybe add a quick response to tell the client the transfer is okay.
    resp_obj = connection.recv_obj()
    resp_type = resp_obj.type
    check_response(CLIENT_FILE_TRANSFER, resp_type)

    recv_file_tree(host_obj, resp_obj, cloud, connection, db)
    mylog('[{}]bottom of handle_recv_file_from_client(...,{})'
          .format(client.uuid, msg_obj.__dict__))


def handle_read_file_request(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj
                                  , do_client_read_file)


def do_client_read_file(host_obj, connection, address, msg_obj, client):
    db = get_db()
    cloud = client.cloud

    cloudname = cloud.name
    requested_file = msg_obj.fpath

    requesting_all = requested_file == '/'
    filepath = None
    # if the root is '/', send all of the children of the root
    if requesting_all:
        filepath = cloud.root_directory
        # todo: if they're requesting all, it's definitely a dir,
        # which is an error
    else:
        filepath = os.path.join(cloud.root_directory, requested_file)

    # FIXME: Make sure paths are limited to children of the root

    req_file_stat = None
    try:
        req_file_stat = os.stat(filepath)
    except Exception:
        err_msg = FileDoesNotExistErrorMessage()
        connection.send_obj(err_msg)
        # connection.close()
        return

    relative_pathname = os.path.relpath(filepath, cloud.root_directory)

    rd = host_obj.client_access_check_or_close(connection, client.uuid, cloud,
                                               relative_pathname, READ_ACCESS)
    if not rd.success:
        return

    req_file_is_dir = S_ISDIR(req_file_stat.st_mode)
    if req_file_is_dir:
        err_msg = FileIsDirErrorMessage()
        connection.send_obj(err_msg)
        # connection.close()
    else:
        # send RFP - ReadFileResponse
        req_file_size = req_file_stat.st_size
        requested_file = open(filepath, 'rb')
        response = ReadFileResponseMessage(client.uuid, relative_pathname,
                                           req_file_size)
        connection.send_obj(response)
        mylog(
            'sent RFRp:{}, now sending file bytes'.format(response.serialize()))
        l = 1
        total_len = 0
        num_MB = int(math.floor(req_file_size / (1024 * 1024)))
        transfer_size = 1024 + (10 * 1024 * num_MB)
        num_transfers = 0
        # send file bytes
        while l > 0:
            new_data = requested_file.read(transfer_size)
            sent_len = connection.send_next_data(new_data)
            l = sent_len
            total_len += sent_len
            num_transfers += 1
            if (num_transfers % 128 == 0) and num_transfers > 1:
                mylog('sent {} blobs of <{}> ({}/{}B total)'
                      .format(num_transfers, filepath, total_len,
                              req_file_size))
                time.sleep(.1)

        mylog(
            '(RFQ)[{}]Sent <{}> data to [{}]'
            .format(cloud.my_id_from_remote, filepath, client.uuid)
        )

        requested_file.close()
    mylog('[{}]bottom of handle_read_file_request(...,{})'
          .format(client.uuid, msg_obj))


def list_files_handler(host_obj, connection, address, msg_obj):
    mylog('list_files_handler')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_list_files)


def client_message_wrapper(host_obj, connection, address, msg_obj, callback):
    session_id = msg_obj.sid
    cloudname = msg_obj.cname
    cloud_uname = None  # todo:15
    db = get_db()

    rd = validate_or_get_client_session(db, session_id, cloud_uname, cloudname)
    if not rd.success:
        response = ClientAuthErrorMessage(rd.data)
        send_error_and_close(response, connection)
        return
    else:
        mylog('valid client session')
        client = rd.data
        cloud = client.cloud
        mylog('client.cloud={}'.format(client.cloud))
        if cloud is None:
            # todo:17 The cloud could have been deleted while a client had it
            err = InvalidStateMessage('Somehow the client object did not have '
                                      'a cloud associated with it.')
            mylog(err.message, '31')
            send_error_and_close(err, connection)
            return

        callback(host_obj, connection, address, msg_obj, client)


def do_client_list_files(host_obj, connection, address, msg_obj, client):
    mylog('do_client_list_files')
    cloud = client.cloud
    cloudname = cloud.name
    rel_path = msg_obj.fpath
    session_id = client.uuid
    full_path = cloud.translate_relative_path(rel_path)
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, READ_ACCESS)
    if rd.success:
        mylog('Responding successfully to ClientListFiles')
        resp = ListFilesResponseMessage(cloudname, session_id, rel_path,
                                        full_path)
        connection.send_obj(resp)
    else:
        # the access check will send error
        pass



def handle_client_add_owner(host_obj, connection, address, msg_obj):
    mylog('handle_client_add_owner')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_add_owner)


def do_client_add_owner(host_obj, connection, address, msg_obj, client):
    cloud = client.cloud
    cloudname = cloud.name
    session_id = client.uuid
    new_owner_id = msg_obj.new_user_id
    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        return

    if not private_data.has_owner(client.user_id):
        msg = 'User [{}] is not an owner of the cloud "{}"'.format(client.user_id, cloudname)
        err = AddOwnerFailureMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        return
    rd = cloud.get_remote_conn()
    if rd.success:
        remote_conn = rd.data
        request = msg_obj
        # todo:24 too lazy to do now
        remote_conn.send_obj(request)
        response = remote_conn.recv_obj()
        if response.type == ADD_OWNER_SUCCESS:
            rd = Success()
        else:
            rd = Error(response.message)
    if not rd.success:
        msg = 'failed to validate the ADD_OWNER request with the remote, msg={}'.format(rd.data)
        err = AddOwnerFailureMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
    else:
        private_data.add_owner(new_owner_id)
        private_data.commit()
        mylog('Added user [{}] to the owners of {}'.format(new_owner_id, cloudname))
        # todo:15
        response = AddOwnerSuccessMessage(session_id, new_owner_id, 'todo-uname', cloudname)
        connection.send_obj(response)


def handle_client_add_contributor(host_obj, connection, address, msg_obj):
    mylog('handle_client_add_contributor')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_add_contributor)


def do_client_add_contributor(host_obj, connection, address, msg_obj, client):
    cloud = client.cloud
    cloudname = cloud.name
    session_id = client.uuid
    new_user_id = msg_obj.new_user_id
    fpath = msg_obj.fpath
    new_permissions = msg_obj.permissions

    # TODO: make sure the path is a relative path to the cloud

    # TODO: Normalize the path

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        return
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               fpath, SHARE_ACCESS)
    if not rd.success:
        # conn was closed by client_access_check_or_close
        return

    perms = rd.data
    if not permissions_are_sufficient(perms, new_permissions):
        msg = 'Client doesn\'t have permission to give to other user'
        err = AddContributorFailureMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        return
    mylog('Client has sharing permission')
    rd = cloud.get_remote_conn()
    if rd.success:
        remote_conn = rd.data
        # todo:15
        request = AddContributorMessage(cloud.my_id_from_remote, new_user_id, 'todo-uname', cloudname)
        # todo:24 too lazy to do now
        remote_conn.send_obj(request)
        response = remote_conn.recv_obj()
        if response.type == ADD_CONTRIBUTOR_SUCCESS:
            rd = Success()
        else:
            rd = Error(response.message)
    mylog('completed talking to remote, {}'.format(rd))
    if not rd.success:
        msg = 'failed to validate the ADD_ADD_CONTRIBUTOR request with the remote, msg={}'.format(rd.data)
        err = AddContributorFailureMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
    else:
        private_data.add_user_permission(new_user_id, fpath, new_permissions)
        private_data.commit()
        mylog('Added permission {} for user [{}] to file {}:{}'.format(
            new_permissions, new_user_id, cloudname, fpath
        ))
        # todo:15
        response = AddContributorSuccessMessage(new_user_id, 'todo-uname', cloudname)
        connection.send_obj(response)