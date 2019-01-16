import math
import os
import time
from stat import S_ISDIR

import shutil

from common_util import mylog, send_error_and_close, Success, Error, PUBLIC_USER_ID, get_mylog, \
    ResultAndData, RelativeLink
from common.RelativePath import RelativePath
from connections.AbstractConnection import AbstractConnection
from host.PrivateData import READ_ACCESS, SHARE_ACCESS, NO_ACCESS, WRITE_ACCESS, APPEND_ACCESS
from host.function.recv_files import recv_file_transfer, do_recv_file_transfer
from host.models.Cloud import Cloud
from host.models.Client import Client
from host.util import check_response, validate_or_get_client_session, \
    permissions_are_sufficient, get_clouds_by_name
from messages import *
from messages.util import make_ls_array, make_stat_dict
from msg_codes import *


################################################################################
# CLIENT_FILE_TRANSFER
def handle_recv_file_from_client(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj
                                  , do_recv_file_from_client)


def do_recv_file_from_client(host_obj, connection, address, msg_obj, client, cloud):
    db = host_obj.get_db()
    _log = get_mylog()
    client_uuid = client.uuid if client is not None else None
    client_uid = client.user_id if client else PUBLIC_USER_ID
    file_isdir = msg_obj.isdir
    file_size = msg_obj.fsize
    file_path = msg_obj.fpath

    # todo: maybe add a quick response to tell the client the transfer is okay.
    #   Originally, there was a ClientFilePut followed by a ClientFileTransfer.

    rel_path = RelativePath()
    rd = rel_path.from_relative(file_path)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(file_path)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        host_obj.log_client(client, 'write', cloud, rel_path, 'error')
        send_error_and_close(err, connection)
        return Error(err)

    # make sure that it's not the private data file
    # make sure we have appropriate permissions
    #   if it's a existing file, we'll need to make sure we have write access on that file
    #   otherwise, the next existing parent must have either write or append permission
    #   if we're creating a new file, and the parent only has append permission, then we should
    # SHOULD WE? make the child write access?
    # or should it be the responsibility of the client to also set that permission?
    # The user will likely not be able to modify the permissions of the cloud,
    #   so they likely wont be able to append the file then chmod the file to
    #   have write-access. However, there'd also be no way for the owner (of the
    #   append-only dir) to pre-authorize any changes in ownership.
    # lets give them write permissions. Yes. Lets.
    # but then they could append a new dir, and then that would have write
    #   access, and then they could go and write whatever the hell they want
    # But I guess that's not technically any worse than letting them append as
    #   many children as they want.

    full_path = rel_path.to_absolute(cloud.root_directory)

    if host_obj.is_private_data_file(full_path, cloud):
        msg = 'Clients are not allowed to modify the {} file'.format(rel_path.to_string())
        err = SystemFileWriteErrorMessage(msg)
        _log.debug(err)
        host_obj.log_client(client, 'write', cloud, rel_path, 'error')
        send_error_and_close(err, connection)
        return Error(err)

    appending_new = False
    if os.path.exists(full_path):
        rd = host_obj.client_access_check_or_close(connection, client_uuid, cloud,
                                                   rel_path, WRITE_ACCESS)
    else:
        # get_client_permissions will call private_data.get_permissions, which
        #   will traverse top-down to build the users's permissions. If there
        #   are intermediate paths that dont exist, but at least one parent has
        #   append access, get_client_permisssions will know
        permissions = host_obj.get_client_permissions(client_uuid, cloud, rel_path)

        if not permissions_are_sufficient(permissions, WRITE_ACCESS):
            if not permissions_are_sufficient(permissions, APPEND_ACCESS):
                msg = 'Session does not have sufficient permission to access <{}>'.format(rel_path.to_string())
                _log.debug(msg)
                err = InvalidPermissionsMessage(msg)
                host_obj.log_client(client, 'write', cloud, rel_path, 'error')
                send_error_and_close(err, connection)
                return Error(err)
            else:
                # user does have append permission
                appending_new = True
                rd = Success()
        else:
            #user does have write access, this is good
            pass
            rd = Success()

    if rd.success:
        rd = do_recv_file_transfer(host_obj, cloud, connection, rel_path, file_isdir, file_size)

    if rd.success and appending_new:

        private_data = host_obj.get_private_data(cloud)
        if private_data is None:
            msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
            err = InvalidStateMessage(msg)
            _log.debug(err)
            host_obj.log_client(client, 'write', cloud, rel_path, 'error')
            send_error_and_close(err, connection)
            return Error(err)
        private_data.add_user_permission(client_uid, rel_path, WRITE_ACCESS)
        private_data.commit()
        _log.debug('Added permission {} for user [{}] to file {}:{} while appending_new'.format(
            WRITE_ACCESS, client_uid, cloud.cname(), rel_path.to_string()
        ))

    host_obj.log_client(client, 'write', cloud, rel_path, 'success' if rd.success else 'error')
    connection.send_obj(rd.data)


################################################################################
# READ_FILE_REQUEST
def handle_read_file_request(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj
                                  , do_client_read_file)


def do_client_read_file(host_obj, connection, address, msg_obj, client, cloud, lookup_permissions=True):
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

    if lookup_permissions:
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


################################################################################
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


################################################################################
def client_link_wrapper(host_obj, connection, address, msg_obj
                       , callback  # type: (HostController, AbstractConnection, object, BaseMessage, Client, Cloud) -> ResultAndData
                       ):
    # type: (HostController, AbstractConnection, object, BaseMessage, ...) -> None
    session_id = msg_obj.sid
    link_id = msg_obj.link_string
    db = host_obj.get_db()
    _log = get_mylog()
    # Search all of the private datas for one that has the given link.
    clouds = host_obj.find_link_clouds(link_id)
    if len(clouds) < 1:
        err = '{} is not a link on this device'.format(link_id)
        _log.debug(err)
        msg = InvalidStateMessage(err)
        connection.send_obj(msg)
        connection.close()
    cloud = clouds[0]
    # validate that cloud as the one the client was prepped to find
    # TODO: this is very similar to the body of client_message_wrapper
    rd = validate_or_get_client_session(db, session_id, cloud.uname(), cloud.cname())
    if not rd.success:
        response = ClientAuthErrorMessage(rd.data)
        send_error_and_close(response, connection)
        return
    client = rd.data
    # None is the public user
    if client is not None:
        # refresh the session:
        rd = cloud.get_remote_conn()
        if rd.success:
            refresh = ClientSessionRefreshMessage(session_id)
            rd.data.send_obj(refresh)
            rd.data.close()
        else:
            mylog('Failed to refresh client session.')

    return callback(host_obj, connection, address, msg_obj, client, cloud)


################################################################################
def list_files_handler(host_obj, connection, address, msg_obj):
    mylog('list_files_handler')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_list_files)


def do_client_list_files(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    cloudname = cloud.name
    session_id = client.uuid if client is not None else None
    client_uid = client.user_id if client else PUBLIC_USER_ID

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        host_obj.log_client(client, 'ls', cloud, None, 'error')
        send_error_and_close(err, connection)
        return

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
        if not os.path.exists(full_path):
            resp = FileDoesNotExistErrorMessage()
            host_obj.log_client(client, 'ls', cloud, rel_path, 'error')

        elif not os.path.isdir(full_path):
            mylog('Responding to ClientListFiles with error - {} is a file, not dir.'.format(rel_path.to_string()))
            resp = FileIsNotDirErrorMessage()
            host_obj.log_client(client, 'ls', cloud, rel_path, 'error')

        else:
            mylog('Responding successfully to ClientListFiles')
            resp = ListFilesResponseMessage(cloudname, session_id, rel_path.to_string())
            resp.stat = make_stat_dict(rel_path, private_data, cloud, client_uid)
            resp.ls = make_ls_array(rel_path, private_data, cloud, client_uid)
            host_obj.log_client(client, 'ls', cloud, rel_path, 'success')

        connection.send_obj(resp)
    else:
        # the access check will send error
        host_obj.log_client(client, 'ls', cloud, rel_path, 'error')
        pass


################################################################################
def stat_files_handler(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_stat_files)


def do_client_stat_files(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    cloudname = cloud.name
    session_id = client.uuid if client is not None else None
    client_uid = client.user_id if client else PUBLIC_USER_ID

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        host_obj.log_client(client, 'stat', cloud, None, 'error')
        send_error_and_close(err, connection)
        return Error(err)

    rel_path = RelativePath()
    rd = rel_path.from_relative(msg_obj.fpath)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(msg_obj.fpath)
        err = InvalidStateMessage(msg)
        _log.debug(err)
        send_error_and_close(err, connection)
        host_obj.log_client(client, 'stat', cloud, rel_path, 'error')
        return Error(err)

    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, READ_ACCESS)
    if rd.success:
        full_path = rel_path.to_absolute(cloud.root_directory)
        if not os.path.exists(full_path):
            resp = FileDoesNotExistErrorMessage()
            host_obj.log_client(client, 'stat', cloud, rel_path, 'error')

        # elif not os.path.isdir(full_path):
        #     mylog('Responding to ClientListFiles with error - {} is a file, not dir.'.format(rel_path.to_string()))
        #     resp = FileIsNotDirErrorMessage()
        #     host_obj.log_client(client, 'ls', cloud, rel_path, 'error')

        else:
            mylog('Responding successfully to ClientStatFile')
            resp = StatFileResponseMessage(cloudname, session_id, rel_path.to_string())
            resp.stat = make_stat_dict(rel_path, private_data, cloud, client_uid)
            # resp.ls = make_ls_array(rel_path, private_data, cloud, client_uid)
            host_obj.log_client(client, 'stat', cloud, rel_path, 'success')

        connection.send_obj(resp)
        return ResultAndData(resp.type == STAT_FILE_RESPONSE, resp)
    else:
        # the access check will send error
        host_obj.log_client(client, 'stat', cloud, rel_path, 'error')
        return rd

################################################################################

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

################################################################################

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
################################################################################

def do_client_make_directory(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    real_message = ClientFileTransferMessage(msg_obj.sid
                                             , msg_obj.cloud_uname
                                             , msg_obj.cname
                                             , os.path.join(msg_obj.root, msg_obj.dir_name)
                                             , 0
                                             , True)
    _log.debug('converted={}'.format(real_message.serialize()))
    return do_recv_file_from_client(host_obj, connection, address, real_message, client, cloud)
    # return recv_file_transfer(host_obj, real_message, cloud, connection, host_obj.get_db(), True)


def handle_client_make_directory(host_obj, connection, address, msg_obj):
    mylog('handle_client_make_directory')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_make_directory)

################################################################################

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

    # private_data = host_obj.get_private_data(cloud)
    # if private_data is None:
    #     msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
    #     err = InvalidStateMessage(msg)
    #     mylog(err.message, '31')
    #     send_error_and_close(err, connection)
    #     return
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, NO_ACCESS)
    if not rd.success:
        # conn was closed by client_access_check_or_close
        return rd

    perms = rd.data
    _log.debug('{} has {} permission for {}'.format(client_uid, perms, rel_path.to_string()))
    resp = ClientGetPermissionsResponseMessage(perms)
    connection.send_obj(resp)

def handle_client_get_permissions(host_obj, connection, address, msg_obj):
    mylog('handle_client_get_permissions')
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_get_permissions)

################################################################################

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
    _log.debug('Creating a link to {}'.format(rel_path.to_string()))
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
    _log.debug('Got remote connection')
    remote_conn.send_obj(remote_req)
    remote_resp = remote_conn.recv_obj()
    if remote_resp.type is not HOST_RESERVE_LINK_RESPONSE:
        msg = 'Remote failed to reserve link for us'
        _log.error(msg)
        host_obj.log_client(client, 'link', cloud, rel_path, 'error')
        connection.send_obj(InvalidStateMessage(msg))
        connection.close()
        return Error(msg)
    _log.debug('Got link from remote')
    link_str = remote_resp.link_string
    # Create the link in the private data
    private_data.add_link(rel_path, link_str)
    _log.debug('Committing .nebs to add link {}->{}'.format(link_str, rel_path.to_string()))
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
    link_str = msg_obj.link_string

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

    rd = host_obj.client_link_access_check_or_close(connection, session_id, cloud,
                                                    link_str, READ_ACCESS)
    if not rd.success:
        # conn was closed by client_access_check_or_close
        return

    # get the path rom the link
    rel_path = RelativePath()
    path = private_data.get_path_from_link(link_str)
    if path is None:
        msg = 'The link {} is not valid for this cloud'.format(link_str)
        err = LinkDoesNotExistMessage(msg)
        _log.error(err.message)
        host_obj.log_client(client, 'read-link', cloud, link_str, 'error')
        send_error_and_close(err, connection)
        return

    rel_path.from_relative(path)
    # construct a ReadFile message, using the path from the link
    translated = ReadFileRequestMessage(session_id, cloud.uname(), cloud.cname(), rel_path.to_string())

    return do_client_read_file(host_obj, connection, address, translated, client, cloud, lookup_permissions=False)


def handle_client_read_link(host_obj, connection, address, msg_obj):
    return client_link_wrapper(host_obj, connection, address, msg_obj,
                               do_client_read_link)
################################################################################

# Things to consider while deleting:
# Is the file a dir or plain file?
# is it empty?
# are we recursivly deleting?
# removing the path from the .nebs
#   Deleting the link?
#       The file is gone now, probably don't want that link pointing at the same name
#   Actually, won't need to do this, when the local udates thread wakes up it
#       will take care of all this.

################################################################################
def do_client_delete_file(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    user_id = client.user_id if client else PUBLIC_USER_ID
    session_id = client.uuid if client else None
    fpath = msg_obj.path
    rel_path = RelativePath()
    rd = rel_path.from_relative(fpath)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(fpath)
        err = InvalidStateMessage(msg)
        send_error_and_close(err, connection)
        host_obj.log_client(client, 'rm', cloud, rel_path, 'error')
        return Error(err)

    # TODO Does the client need access to write the file, or the parent directory?
    # Technically they're modifying the parent dir
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, WRITE_ACCESS)
    if not rd.success:
        # conn was closed by client_access_check_or_close
        return

    full_path = rel_path.to_absolute(cloud.root_directory)
    if not os.path.exists(full_path):
        resp = FileDoesNotExistErrorMessage()
        host_obj.log_client(client, 'rm', cloud, rel_path, 'error')

    elif os.path.isdir(full_path):
        resp = FileIsDirErrorMessage()
        host_obj.log_client(client, 'rm', cloud, rel_path, 'error')

    else:
        try:
            os.remove(full_path)
            resp = ClientDeleteResponseMessage()
        except IOError as e:
            msg = 'error deleting {}, "{}"', rel_path.to_string(), e.message
            _log.error(msg)
            resp = UnknownIoErrorMessage(msg)

    host_obj.log_client(client, 'rm', cloud, rel_path, 'success' if resp.type == CLIENT_DELETE_RESPONSE else 'error')
    connection.send_obj(resp)


def handle_client_delete_file(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                               do_client_delete_file)
################################################################################


################################################################################
def do_client_remove_dir(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    user_id = client.user_id if client else PUBLIC_USER_ID
    session_id = client.uuid if client else None
    fpath = msg_obj.path
    recurse = msg_obj.recursive
    rel_path = RelativePath()
    rd = rel_path.from_relative(fpath)
    if not rd.success:
        msg = '{} is not a valid cloud path'.format(fpath)
        err = InvalidStateMessage(msg)
        send_error_and_close(err, connection)
        host_obj.log_client(client, 'rmdir', cloud, rel_path, 'error')
        return Error(err)

    # TODO Does the client need access to write the file, or the parent directory?
    # Technically they're modifying the parent dir
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, WRITE_ACCESS)
    if not rd.success:
        # conn was closed by client_access_check_or_close
        return

    full_path = rel_path.to_absolute(cloud.root_directory)
    if not os.path.exists(full_path):
        resp = FileDoesNotExistErrorMessage()
        host_obj.log_client(client, 'rmdir', cloud, rel_path, 'error')

    elif not os.path.isdir(full_path):
        resp = FileIsDirErrorMessage()
        host_obj.log_client(client, 'rmdir', cloud, rel_path, 'error')
    else:
        subdirs = os.listdir(full_path)
        if len(subdirs) > 0 and not recurse:
            resp = DirIsNotEmptyMessage()
        elif len(subdirs) > 0 and recurse:
            try:
                shutil.rmtree(full_path)
                resp = ClientDeleteResponseMessage()
            except OSError as e:
                msg = 'error deleting {}, "{}"', rel_path.to_string(), e.message
                _log.error(msg)
                resp = UnknownIoErrorMessage(msg)
        else:  # len subdirs == 0
            try:
                os.rmdir(full_path)
                resp = ClientDeleteResponseMessage()
            except IOError as e:
                msg = 'error deleting {}, "{}"', rel_path.to_string(), e.message
                _log.error(msg)
                resp = UnknownIoErrorMessage(msg)

    host_obj.log_client(client, 'rmdir', cloud, rel_path, 'success' if resp.type == CLIENT_DELETE_RESPONSE else 'error')
    connection.send_obj(resp)


def handle_client_remove_dir(host_obj, connection, address, msg_obj):
    return client_message_wrapper(host_obj, connection, address, msg_obj,
                                  do_client_remove_dir)
################################################################################


################################################################################
def do_client_set_link_permissions(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    user_id = client.user_id if client else PUBLIC_USER_ID
    session_id = client.uuid if client else None
    link_str = msg_obj.link_string
    permissions = msg_obj.permissions

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        host_obj.log_client(client, 'chmod-link', cloud, RelativeLink(link_str), 'error')
        send_error_and_close(err, connection)
        return Error(msg)

    # get the path from the link
    rel_path = RelativePath()
    path = private_data.get_path_from_link(link_str)
    if path is None:
        msg = 'The link {} is not valid for this cloud'.format(link_str)
        err = LinkDoesNotExistMessage(msg)
        _log.error(err.message)
        host_obj.log_client(client, 'chmod-link', cloud, RelativeLink(link_str), 'error')
        send_error_and_close(err, connection)
        return
    rel_path.from_relative(path)

    # Using the actual file, check if the client has access to share the file.
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, SHARE_ACCESS)
    if not rd.success:
        return rd

    rd = private_data.set_link_permissions(link_str, permissions)
    if rd.success:
        private_data.commit()
    response = ClientSetLinkPermissionsSuccessMessage() if rd.success else LinkDoesNotExistMessage()
    host_obj.log_client(client, 'chmod-link', cloud, RelativeLink(link_str), 'success' if rd.success else 'error')
    connection.send_obj(response)


def handle_client_set_link_permissions(host_obj, connection, address, msg_obj):
    return client_link_wrapper(host_obj, connection, address, msg_obj,
                               do_client_set_link_permissions)
################################################################################

################################################################################
def do_client_add_user_to_link(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    user_id = client.user_id if client else PUBLIC_USER_ID
    session_id = client.uuid if client else None
    link_str = msg_obj.link_string
    new_uid = msg_obj.user_id

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        host_obj.log_client(client, 'chown+link', cloud, RelativeLink(link_str), 'error')
        send_error_and_close(err, connection)
        return Error(msg)

    # get the path from the link
    rel_path = RelativePath()
    path = private_data.get_path_from_link(link_str)
    if path is None:
        msg = 'The link {} is not valid for this cloud'.format(link_str)
        err = LinkDoesNotExistMessage(msg)
        _log.error(err.message)
        host_obj.log_client(client, 'chown+link', cloud, RelativeLink(link_str), 'error')
        send_error_and_close(err, connection)
        return
    rel_path.from_relative(path)

    # Using the actual file, check if the client has access to share the file.
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, SHARE_ACCESS)
    if not rd.success:
        return rd

    rd = private_data.add_user_to_link(link_str, new_uid)
    if rd.success:
        private_data.commit()
    response = ClientSetLinkPermissionsSuccessMessage() if rd.success else LinkDoesNotExistMessage()
    host_obj.log_client(client, 'chown+link', cloud, RelativeLink(link_str), 'success' if rd.success else 'error')
    connection.send_obj(response)


def handle_client_add_user_to_link(host_obj, connection, address, msg_obj):
    return client_link_wrapper(host_obj, connection, address, msg_obj,
                               do_client_add_user_to_link)
################################################################################


################################################################################
def do_client_remove_user_from_link(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    user_id = client.user_id if client else PUBLIC_USER_ID
    session_id = client.uuid if client else None
    link_str = msg_obj.link_string
    new_uid = msg_obj.user_id

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        host_obj.log_client(client, 'chown-link', cloud, RelativeLink(link_str), 'error')
        send_error_and_close(err, connection)
        return Error(msg)

    # get the path from the link
    rel_path = RelativePath()
    path = private_data.get_path_from_link(link_str)
    if path is None:
        msg = 'The link {} is not valid for this cloud'.format(link_str)
        err = LinkDoesNotExistMessage(msg)
        _log.error(err.message)
        host_obj.log_client(client, 'chown-link', cloud, RelativeLink(link_str), 'error')
        send_error_and_close(err, connection)
        return
    rel_path.from_relative(path)

    # Using the actual file, check if the client has access to share the file.
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, SHARE_ACCESS)
    if not rd.success:
        return rd

    rd = private_data.remove_user_from_link(link_str, new_uid)
    if rd.success:
        private_data.commit()
    response = ClientSetLinkPermissionsSuccessMessage() if rd.success else LinkDoesNotExistMessage()
    host_obj.log_client(client, 'chown-link', cloud, RelativeLink(link_str), 'success' if rd.success else 'error')
    connection.send_obj(response)


def handle_client_remove_user_from_link(host_obj, connection, address, msg_obj):
    return client_link_wrapper(host_obj, connection, address, msg_obj,
                               do_client_remove_user_from_link)
################################################################################


################################################################################
def do_client_get_link_permissions(host_obj, connection, address, msg_obj, client, cloud):
    _log = get_mylog()
    user_id = client.user_id if client else PUBLIC_USER_ID
    session_id = client.uuid if client else None
    link_str = msg_obj.link_string

    private_data = host_obj.get_private_data(cloud)
    if private_data is None:
        msg = 'Somehow the cloud doesn\'t have a privatedata associated with it'
        err = InvalidStateMessage(msg)
        mylog(err.message, '31')
        # host_obj.log_client(client, 'chown+link', cloud, RelativeLink(link_str), 'error')
        send_error_and_close(err, connection)
        return Error(msg)

    # get the path from the link
    rel_path = RelativePath()
    path = private_data.get_path_from_link(link_str)
    if path is None:
        msg = 'The link {} is not valid for this cloud'.format(link_str)
        err = LinkDoesNotExistMessage(msg)
        _log.error(err.message)
        # host_obj.log_client(client, 'chown+link', cloud, RelativeLink(link_str), 'error')
        send_error_and_close(err, connection)
        return
    rel_path.from_relative(path)

    # TODO: Get the permissions of the backing file too, and OR them with the permissions on the link.
    rd = host_obj.client_access_check_or_close(connection, session_id, cloud,
                                               rel_path, NO_ACCESS)
    if not rd.success:
        return rd
    file_perms = rd.data
    rd = private_data.get_link_full_permissions(link_str)
    if rd.success:
        link_perms = rd.data[0]
        users = rd.data[1]
        response = ClientGetLinkPermissionsResponseMessage(link_perms | file_perms, users)
    else:
        response = LinkDoesNotExistMessage()
    # host_obj.log_client(client, 'chown+link', cloud, RelativeLink(link_str), 'success' if rd.success else 'error')
    connection.send_obj(response)


def handle_client_get_link_permissions(host_obj, connection, address, msg_obj):
    return client_link_wrapper(host_obj, connection, address, msg_obj,
                               do_client_get_link_permissions)
################################################################################
