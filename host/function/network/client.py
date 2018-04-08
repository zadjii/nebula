import math
import os
import time
from stat import S_ISDIR

from common_util import mylog, send_error_and_close, Success, Error, PUBLIC_USER_ID, RelativePath, get_mylog, ResultAndData
from connections.AbstractConnection import AbstractConnection
from host.PrivateData import READ_ACCESS, SHARE_ACCESS, NO_ACCESS, WRITE_ACCESS
from host.function.recv_files import recv_file_tree, recv_file_transfer
from host.models.Cloud import Cloud
from host.models.Client import Client
from host.util import check_response, validate_or_get_client_session, \
    permissions_are_sufficient, get_clouds_by_name
from messages import *
from msg_codes import *


def handle_recv_file_from_client(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj
                                  , do_recv_file_from_client)


def do_recv_file_from_client(host_obj, connection, address, msg_obj, client, cloud):
    db = host_obj.get_db()
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


def do_client_read_file(host_obj, connection, address, msg_obj, client, cloud):
    db = host_obj.get_db()
    _log = get_mylog()
    client_uuid = client.uuid if client is not None else None
    # cloud = client.cloud

    cloudname = cloud.name
    requested_file = msg_obj.fpath

    rel_path = RelativePath()
    rd = rel_path.from_relative(requested_file)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(requested_file)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        send_error_and_close(err, connection)
        host_obj.log_client(client, 'read', cloud, rel_path, 'error')
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
        host_obj.log_client(client, 'read', cloud, rel_path, 'error')
        # connection.close()
        return

    rd = host_obj.client_access_check_or_close(connection
                                               , client_uuid
                                               , cloud
                                               , rel_path
                                               , READ_ACCESS)
    if not rd.success:
        host_obj.log_client(client, 'read', cloud, rel_path, 'error')
        return

    req_file_is_dir = S_ISDIR(req_file_stat.st_mode)
    if req_file_is_dir:
        err_msg = FileIsDirErrorMessage()
        connection.send_obj(err_msg)
        host_obj.log_client(client, 'read', cloud, rel_path, 'error')
        # connection.close()
    else:
        # send RFP - ReadFileResponse
        req_file_size = req_file_stat.st_size
        requested_file = open(filepath, 'rb')
        response = ReadFileResponseMessage(client_uuid, rel_path.to_string(),
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
        host_obj.log_client(client, 'read', cloud, rel_path, 'success')
    mylog('[{}]bottom of handle_read_file_request(...,{})'
          .format(client.uuid, msg_obj))


def list_files_handler(host_obj, connection, address, msg_obj):
    mylog('list_files_handler')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_list_files)


def client_message_wrapper(host_obj, connection, address, msg_obj
                           , callback  # type: (HostController, AbstractConnection, object, BaseMessage, Client, Cloud) -> ResultAndData
                           ):
    # type: (HostController, AbstractConnection, object, BaseMessage, ...) -> None
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
        cloud = None
        if client is None:
            # The client is the public client. Callers should be prepared to handle
            # the public client case.
            clouds = get_clouds_by_name(db, cloud_uname, cloudname)
            if len(clouds) > 0:
                cloud = clouds[0]
            else:
                err = InvalidStateMessage('Public client came for {}/{}, but was unable to find it.'.format(cloud_uname, cloudname))
                mylog(err.message, '31')
                send_error_and_close(err, connection)
                return
        else:
            cloud = client.cloud
            mylog('client.cloud={}'.format(client.cloud.full_name()))
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

        return callback(host_obj, connection, address, msg_obj, client, cloud)


def do_client_list_files(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    _log.debug('do_client_list_files')
    cloudname = cloud.name
    session_id = client.uuid if client is not None else None

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
        host_obj.log_client(client, 'ls', cloud, rel_path, 'error')
        return

    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, READ_ACCESS)
    if rd.success:
        full_path = rel_path.to_absolute(cloud.root_directory)
        if not os.path.isdir(full_path):
            mylog('Responding to ClientListFiles with error - {} is a file, not dir.'.format(rel_path.to_string()))
            resp = FileIsNotDirErrorMessage()
            host_obj.log_client(client, 'ls', cloud, rel_path, 'error')
        else:
            mylog('Responding successfully to ClientListFiles')
            resp = ListFilesResponseMessage(cloudname, session_id, rel_path.to_string(),
                                            full_path)

            host_obj.log_client(client, 'ls', cloud, rel_path, 'success')
        connection.send_obj(resp)
    else:
        # the access check will send error
        host_obj.log_client(client, 'ls', cloud, rel_path, 'error')
        pass



def handle_client_add_owner(host_obj, connection, address, msg_obj):
    mylog('handle_client_add_owner')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_add_owner)


def do_client_add_owner(host_obj, connection, address, msg_obj, client, cloud):
    cloudname = cloud.cname()
    session_id = client.uuid if client else None
    client_uid = client.user_id if client else PUBLIC_USER_ID
    new_owner_id = msg_obj.new_user_id
    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        host_obj.log_client(client, 'add-owner', cloud, None, 'error')
        send_error_and_close(err, connection)
        return

    if new_owner_id == PUBLIC_USER_ID:
        msg = 'The public can\'t be a owner of a cloud'
        err = AddOwnerFailureMessage(msg)
        mylog(err.message, '31')
        host_obj.log_client(client, 'add-owner', cloud, None, 'error')
        send_error_and_close(err, connection)
        return
    if not private_data.has_owner(client_uid):
        msg = 'User [{}] is not an owner of the cloud "{}"'.format(client_uid, cloudname)
        err = AddOwnerFailureMessage(msg)
        mylog(err.message, '31')
        host_obj.log_client(client, 'add-owner', cloud, None, 'error')
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
        host_obj.log_client(client, 'add-owner', cloud, None, 'error')
        send_error_and_close(err, connection)
    else:
        private_data.add_owner(new_owner_id)
        private_data.commit()
        mylog('Added user [{}] to the owners of {}'.format(new_owner_id, cloudname))
        # todo:15
        host_obj.log_client(client, 'add-owner', cloud, None, 'success')
        response = AddOwnerSuccessMessage(session_id, new_owner_id, cloud.uname(), cloudname)
        connection.send_obj(response)


def handle_client_add_contributor(host_obj, connection, address, msg_obj):
    mylog('handle_client_add_contributor')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_add_contributor)


def do_client_add_contributor(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    cloudname = cloud.name
    session_id = client.uuid if client else None
    new_user_id = msg_obj.new_user_id
    fpath = msg_obj.fpath
    new_permissions = msg_obj.permissions

    rel_path = RelativePath()
    rd = rel_path.from_relative(fpath)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(fpath)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        host_obj.log_client(client, 'share', cloud, rel_path, 'error')
        send_error_and_close(err, connection)
        return

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        host_obj.log_client(client, 'share', cloud, rel_path, 'error')
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
        host_obj.log_client(client, 'share', cloud, rel_path, 'error')
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
        host_obj.log_client(client, 'share', cloud, rel_path, 'error')
        send_error_and_close(err, connection)
    else:
        # PrivateData will be able to handle the public_user_id
        private_data.add_user_permission(new_user_id, rel_path, new_permissions)
        private_data.commit()
        mylog('Added permission {} for user [{}] to file {}:{}'.format(
            new_permissions, new_user_id, cloudname, fpath
        ))
        host_obj.log_client(client, 'share', cloud, rel_path, 'success')
        response = AddContributorSuccessMessage(new_user_id, cloud.uname(), cloudname)
        connection.send_obj(response)

def do_client_make_directory(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    real_message = ClientFileTransferMessage(msg_obj.sid
                                             , msg_obj.cloud_uname
                                             , msg_obj.cname
                                             , os.path.join(msg_obj.root, msg_obj.dir_name)
                                             , 0
                                             , True)
    _log.debug('converted={}'.format(real_message.serialize()))
    return recv_file_transfer(host_obj, real_message, cloud, connection, host_obj.get_db(), True)


def handle_client_make_directory(host_obj, connection, address, msg_obj):
    mylog('handle_client_make_directory')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_make_directory)


def do_client_get_permissions(host_obj, connection, address, msg_obj, client, cloud):
    # type: (HostController, AbstractConnection, object, ClientGetPermissionsMessage, Client, Cloud) -> object
    _log = get_mylog()
    session_id = client.uuid if client else None
    client_uid = client.user_id if client else PUBLIC_USER_ID
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
    _log.debug('{} has {} permission for {}'.format(client_uid, perms, rel_path.to_string()))
    resp = ClientGetPermissionsResponseMessage(perms)
    connection.send_obj(resp)

def handle_client_get_permissions(host_obj, connection, address, msg_obj):
    mylog('handle_client_get_permissions')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_get_permissions)


def do_client_get_shared_paths(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    user_id = client.user_id if client else PUBLIC_USER_ID

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
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_get_shared_paths)


################################################################################
def do_client_create_link(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    user_id = client.user_id if client else PUBLIC_USER_ID
    session_id = client.uuid if client else None
    rel_path = RelativePath()
    rel_path.from_relative(msg_obj.path)

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        host_obj.log_client(client, 'link', cloud, rel_path, 'error')
        send_error_and_close(err, connection)
        return Error(msg)

    # how do we want to gate this? Owners only? or sharers only?
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, SHARE_ACCESS)
    if not rd.success:
        # conn was closed by client_access_check_or_close
        return rd

    # We'll ask the remote to give us a link id
    remote_req = HostReserveLinkRequestMessage(cloud.uname(), cloud.cname())
    rd = cloud.get_remote_conn()
    if not rd.success:
        msg = 'Failed to connect to remote for {}: {}'.format(cloud.full_name(), rd.data)
        _log.error(msg)
        host_obj.log_client(client, 'link', cloud, rel_path, 'error')
        connection.send_obj(InvalidStateMessage(msg))
        connection.close()
        return Error(msg)
    remote_conn = rd.data
    remote_conn.send_obj(remote_req)
    remote_resp = remote_conn.recv_obj()
    if remote_resp.type is not HOST_RESERVE_LINK_RESPONSE:
        msg = 'Remote failed to reserve link for us'
        _log.error(msg)
        host_obj.log_client(client, 'link', cloud, rel_path, 'error')
        connection.send_obj(InvalidStateMessage(msg))
        connection.close()
        return Error(msg)

    link_str = remote_resp.link_string
    # Create the link in the private data
    private_data.add_link(rel_path, link_str)
    private_data.commit()

    resp = ClientCreateLinkResponseMessage(link_str)
    connection.send_obj(resp)
    host_obj.log_client(client, 'link', cloud, rel_path, 'success')


def handle_client_create_link(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_create_link)
################################################################################


################################################################################
def do_client_read_link(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    user_id = client.user_id if client else PUBLIC_USER_ID
    session_id = client.uuid if client else None
    link_str = msg_obj.link_str

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        host_obj.log_client(client, 'read-link', cloud, link_str, 'error')
        send_error_and_close(err, connection)
        return Error(msg)

    # TODO: how do we handle seperate link permissions here?
    # We're just translating it straight to a normal readfile message

    # get the path rom the link
    rel_path = RelativePath()
    path = private_data.get_path_from_link(link_str)
    if path is None:
        pass

    rel_path.from_relative(path)
    # construct a ReadFile message, using the path from the link
    translated = ReadFileRequestMessage(session_id, cloud.uname(), cloud.cname(), rel_path.to_string())
    # return do_read_file
    return do_client_read_file(host_obj, connection, address, translated, client, cloud)


def handle_client_read_link(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_create_link)
################################################################################
