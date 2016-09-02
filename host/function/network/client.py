import math
import os
import time
from stat import S_ISDIR

from common_util import mylog, send_error_and_close
from host import get_db, Cloud
from host.function.recv_files import recv_file_tree
from host.util import check_response, validate_or_get_client_session
from messages import FileDoesNotExistErrorMessage, FileIsDirErrorMessage, \
    ReadFileResponseMessage, ListFilesResponseMessage, InvalidStateMessage, \
    ClientAuthErrorMessage
from msg_codes import send_generic_error_and_close, CLIENT_FILE_TRANSFER


def handle_recv_file_from_client(connection, address, msg_obj):
    return client_message_wrapper(connection, address, msg_obj
                                  , do_recv_file_from_client)


def do_recv_file_from_client(connection, address, msg_obj, client):
    db = get_db()
    cloud = client.cloud
    cloudname = cloud.name
    # todo: maybe add a quick response to tell the client the reansfer is okay.
    resp_obj = connection.recv_obj()
    resp_type = resp_obj.type
    check_response(CLIENT_FILE_TRANSFER, resp_type)

    recv_file_tree(resp_obj, cloud, connection, db)
    mylog('[{}]bottom of handle_recv_file_from_client(...,{})'
          .format(client.uuid, msg_obj.__dict__))


def handle_read_file_request(connection, address, msg_obj):
    return client_message_wrapper(connection, address, msg_obj
                                  , do_client_read_file)


def do_client_read_file(connection, address, msg_obj, client):
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

    req_file_is_dir = S_ISDIR(req_file_stat.st_mode)
    if req_file_is_dir:
        err_msg = FileIsDirErrorMessage()
        connection.send_obj(err_msg)
        # connection.close()
    else:
        # send RFP - ReadFileResponse
        req_file_size = req_file_stat.st_size
        requested_file = open(filepath, 'rb')
        response = ReadFileResponseMessage(client.uuid, relative_pathname, req_file_size)
        connection.send_obj(response)
        mylog('sent RFRp:{}, now sending file bytes'.format(response.serialize()))
        l = 1
        total_len = 0
        num_MB = int(math.floor(req_file_size/(1024 * 1024)))
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
                      .format(num_transfers, filepath, total_len, req_file_size))
                time.sleep(.1)

        mylog(
            '(RFQ)[{}]Sent <{}> data to [{}]'
            .format(cloud.my_id_from_remote, filepath, client.uuid)
        )

        requested_file.close()
    mylog('[{}]bottom of handle_read_file_request(...,{})'
          .format(client.uuid, msg_obj))


# def list_files_handler(connection, address, msg_obj):
#     session_id = msg_obj.sid
#     cloudname = msg_obj.cname
#     cloud_uname = None # todo:15
#     rel_path = msg_obj.fpath
#     db = get_db()
#
#     rd = validate_or_get_client_session(db, session_id, cloud_uname, cloudname)
#     if not rd.success:
#         response = ClientAuthErrorMessage(rd.data)
#         send_error_and_close(response, connection)
#         return
#     else:
#         client = rd.data
#         cloud = client.cloud
#         if cloud is None:
#             # todo:17 The cloud could have been deleted while a client had it
#             err = InvalidStateMessage('Somehow the client object did not have '
#                                       'a cloud associated with it.')
#             send_error_and_close(err, connection)
#             return
#         full_path = cloud.translate_relative_path(rel_path)
#         resp = ListFilesResponseMessage(cloudname, session_id, rel_path,
#                                         full_path)
#         connection.send_obj(resp)

def list_files_handler(connection, address, msg_obj):
    return client_message_wrapper(connection, address, msg_obj, do_client_list_files)

def client_message_wrapper(connection, address, msg_obj, callback):
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
        if cloud is None:
            # todo:17 The cloud could have been deleted while a client had it
            err = InvalidStateMessage('Somehow the client object did not have '
                                      'a cloud associated with it.')
            send_error_and_close(err, connection)
            return
        callback(connection, address, msg_obj, client)


def do_client_list_files(connection, address, msg_obj, client):
    cloud = client.cloud
    cloudname = cloud.name
    rel_path = msg_obj.fpath
    session_id = client.uuid
    full_path = cloud.translate_relative_path(rel_path)
    resp = ListFilesResponseMessage(cloudname, session_id, rel_path,
                                    full_path)
    connection.send_obj(resp)