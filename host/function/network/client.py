import math
import os
import time
from stat import S_ISDIR

from common_util import mylog, send_error_and_close, Success, Error, PUBLIC_USER_ID, RelativePath, get_mylog
from host.PrivateData import READ_ACCESS, SHARE_ACCESS, NO_ACCESS, WRITE_ACCESS
from host.function.recv_files import recv_file_tree
from host.util import check_response, validate_or_get_client_session, \
    permissions_are_sufficient
from messages import *
from msg_codes import *


def handle_recv_file_from_client(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj
                                  , do_recv_file_from_client)


def do_recv_file_from_client(host_obj, connection, address, msg_obj, client):
    db = host_obj.get_db()
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
    db = host_obj.get_db()
    _log = get_mylog()
    cloud = client.cloud

    cloudname = cloud.name
    requested_file = msg_obj.fpath

    rel_path = RelativePath()
    rd = rel_path.from_relative(requested_file)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(requested_file)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        send_error_and_close(err, connection)
        return

    requesting_all = requested_file == '/'
    filepath = None
    # if the root is '/', send all of the children of the root
    if requesting_all:
        filepath = cloud.root_directory
        # todo: if they're requesting all, it's definitely a dir,
        # which is an error
    else:
        filepath = rel_path.to_absolute(cloud.root_directory)

    try:
        req_file_stat = os.stat(filepath)
    except Exception:
        err_msg = FileDoesNotExistErrorMessage()
        connection.send_obj(err_msg)
        # connection.close()
        return

    rd = host_obj.client_access_check_or_close(connection, client.uuid, cloud,
                                               rel_path, READ_ACCESS)
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
        response = ReadFileResponseMessage(client.uuid, rel_path.to_string(),
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
            if (num_transfers % 127 == 1) and num_transfers >= 1:
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
    cloud_uname = msg_obj.cloud_uname  # todo:15
    db = host_obj.get_db()

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

        # refresh the session:
        rd = cloud.get_remote_conn()
        if rd.success:
            refresh = ClientSessionRefreshMessage(session_id)
            rd.data.send_obj(refresh)
            rd.data.close()
        else:
            mylog('Failed to refresh client session.')

        callback(host_obj, connection, address, msg_obj, client)


def do_client_list_files(host_obj, connection, address, msg_obj, client):
    _log = get_mylog()
    _log.debug('do_client_list_files')
    cloud = client.cloud
    cloudname = cloud.name
    # rel_path = msg_obj.fpath
    session_id = client.uuid
    # full_path = cloud.translate_relative_path(rel_path)

    # todo: I believe this should be more complicated.
    # Say a person has permission to read some children of the directory,
    # but not the directory itself. ls returns ACCESS_ERROR currently.
    # Perhaps it should return the children it can access?
    # though, is this process recursive? What if I ls "/", but only have access to "/foo/bar/..."?

    rel_path = RelativePath()
    rd = rel_path.from_relative(msg_obj.fpath)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(msg_obj.fpath)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        send_error_and_close(err, connection)
        return

    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, READ_ACCESS)
    if rd.success:
        full_path = rel_path.to_absolute(cloud.root_directory)
        if not os.path.isdir(full_path):
            mylog('Responding to ClientListFiles with error - {} is a file, not dir.'.format(rel_path.to_string()))
            resp = FileIsNotDirErrorMessage()
        else:
            mylog('Responding successfully to ClientListFiles')
            resp = ListFilesResponseMessage(cloudname, session_id, rel_path.to_string(),
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
    cloudname = cloud.cname()
    session_id = client.uuid
    new_owner_id = msg_obj.new_user_id
    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        return

    if new_owner_id == PUBLIC_USER_ID:
        msg = 'The public can\'t be a owner of a cloud'
        err = AddOwnerFailureMessage(msg)
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
        response = AddOwnerSuccessMessage(session_id, new_owner_id, cloud.uname(), cloudname)
        connection.send_obj(response)


def handle_client_add_contributor(host_obj, connection, address, msg_obj):
    mylog('handle_client_add_contributor')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_add_contributor)


def do_client_add_contributor(host_obj, connection, address, msg_obj, client):
    _log = get_mylog()
    cloud = client.cloud
    cloudname = cloud.name
    session_id = client.uuid
    new_user_id = msg_obj.new_user_id
    fpath = msg_obj.fpath
    new_permissions = msg_obj.permissions

    rel_path = RelativePath()
    rd = rel_path.from_relative(fpath)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(fpath)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        send_error_and_close(err, connection)
        return

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        return
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, SHARE_ACCESS)
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
        request = AddContributorMessage(cloud.my_id_from_remote, new_user_id, cloud.uname(), cloudname)
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
        # PrivateData will be able to handle the public_user_id
        private_data.add_user_permission(new_user_id, rel_path, new_permissions)
        private_data.commit()
        mylog('Added permission {} for user [{}] to file {}:{}'.format(
            new_permissions, new_user_id, cloudname, fpath
        ))
        response = AddContributorSuccessMessage(new_user_id, cloud.uname(), cloudname)
        connection.send_obj(response)

def do_client_make_directory(host_obj, connection, address, msg_obj, client):
    _log = get_mylog()
    cloud = client.cloud
    session_id = client.uuid
    root_path = msg_obj.root
    child_path = msg_obj.dir_name

    root_rel_path = RelativePath()
    rd = root_rel_path.from_relative(root_path)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(root_path)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        send_error_and_close(err, connection)
        return
    child_rel_path = RelativePath()
    rd = child_rel_path.from_relative(child_path)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(child_path)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        send_error_and_close(err, connection)
        return

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        return
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               root_rel_path, WRITE_ACCESS)
    if not rd.success:
        # conn was closed by client_access_check_or_close
        return

    full_path = root_rel_path.to_absolute(cloud.root_directory)
    full_path = child_rel_path.to_absolute(full_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
        resp = ClientMakeDirectoryResponseMessage()
    else:
        resp = FileAlreadyExistsMessage()

    connection.send_obj(resp)

def handle_client_make_directory(host_obj, connection, address, msg_obj):
    mylog('handle_client_add_contributor')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_make_directory)


def do_client_get_permissions(host_obj, connection, address, msg_obj, client):
    # type: (HostController, AbstractConnection, object, ClientGetPermissionsMessage, Client) -> object
    _log = get_mylog()
    cloud = client.cloud
    session_id = client.uuid
    fpath = msg_obj.path

    rel_path = RelativePath()
    rd = rel_path.from_relative(fpath)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(fpath)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        send_error_and_close(err, connection)
        return

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        return
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, NO_ACCESS)
    if not rd.success:
        # conn was closed by client_access_check_or_close
        return

    perms = rd.data
    _log.debug('{} has {} permission for {}'.format(client.user_id, perms, rel_path.to_string()))
    resp = ClientGetPermissionsResponseMessage(perms)
    connection.send_obj(resp)

def handle_client_get_permissions(host_obj, connection, address, msg_obj):
    mylog('handle_client_add_contributor')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_get_permissions)


def do_client_get_shared_paths(host_obj, connection, address, msg_obj, client):
    _log = get_mylog()
    cloud = client.cloud
    user_id = client.user_id

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        return

    resp = ClientGetSharedPathsResponseMessage(private_data.get_user_permissions(user_id))
    connection.send_obj(resp)

def handle_client_get_shared_paths(host_obj, connection, address, msg_obj):
    mylog('handle_client_add_contributor')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_get_shared_paths)