import sys
from datetime import datetime

from common_util import ResultAndData, send_error_and_close
from host import get_db, Cloud, IncomingHostEntry
from host.function.network.client import handle_recv_file_from_client, \
    handle_read_file_request, list_files_handler
# from host.function.network.ls_handler import list_files_handler
from host.function.recv_files import recv_file_tree
from host.function.send_files import send_tree
from host.util import check_response, mylog, validate_host_id
from messages import HostVerifyHostFailureMessage, HostVerifyHostRequestMessage
from msg_codes import *

__author__ = 'Mike'

def verify_host(db, cloud_uname, cname, local_id, other_id):
    """
    Returns either (False, error_string) or (True, matching_mirror)
    """
    rd = ResultAndData(False, None)
    # I'm naming this a mirror because that's what it is.
    # The other host was told to come look for a particular mirror here.
    # if that mirror isn't here, (but another mirror of that cloud is), don't
    # process this request.
    mirror = db.session.query(Cloud).filter_by(my_id_from_remote=local_id).first()
    if mirror is None:
        err = 'That mirror isn\'t on this host.'
        rd = ResultAndData(False, err)
    else:
        rd = mirror.get_remote_conn()
        if rd.success:
            rem_conn = rd.data
            msg = HostVerifyHostRequestMessage(local_id, other_id, cloud_uname, cname)
            try:
                rem_conn.send_obj(msg)
                response = rem_conn.recv_obj()
                if response.type == HOST_VERIFY_HOST_SUCCESS:
                    rd = ResultAndData(True, mirror)
                elif response.type == HOST_VERIFY_HOST_FAILURE:
                    rd = ResultAndData(False, 'Remote responded with failure: "{}"'.format(response.message))
                else:
                    rd = ResultAndData(False, 'Unknown error while attempting to verify host')
            except Exception, e:
                rd = ResultAndData(False, e)
    return rd


def handle_fetch(connection, address, msg_obj):
    db = get_db()
    # the id's are swapped because they are named from the origin host's POV.
    other_id = msg_obj.my_id
    local_id = msg_obj.other_id
    cloudname = msg_obj.cname
    cloud_uname = None  # todo:15
    requested_root = msg_obj.root

    # Go to the remote, ask them if the fetching host is ok'd to be here.
    rd = verify_host(db, cloud_uname, cloudname, local_id, other_id)
    if not rd.success:
        err = HostVerifyHostFailureMessage(rd.data)
        send_error_and_close(err, connection)
        return

    matching_mirror = rd.data

    their_ip = address[0]
    mylog('The connected host is via IP="{}"'.format(their_ip))

    send_tree(other_id, matching_mirror, requested_root, connection)
    mylog('Bottom of handle_fetch', '32')


def handle_recv_file(connection, address, msg_obj):
    db = get_db()
    my_id = msg_obj.tid
    cloudname = msg_obj.cname
    updated_file = msg_obj.fpath
    their_ip = address[0]

    rd = validate_host_id(db, my_id, connection)
    # validate_host_id will raise an exception if there is no cloud
    matching_id_clouds = rd.data
    # matching_id_clouds = db.session.query(Cloud)\
    #     .filter(Cloud.my_id_from_remote == my_id)
    # if matching_id_clouds.count() <= 0:
    #     send_generic_error_and_close(connection)
    #     raise Exception(
    #         'Received a message intended for id={},'
    #         ' but I don\'t have any clouds with that id'
    #         .format(my_id)
    #     )

    matching_cloud = matching_id_clouds.filter_by(name=cloudname).first()
    if matching_cloud is None:
        send_generic_error_and_close(connection)
        raise Exception(
            'host came asking for cloudname=\'' + cloudname + '\''
            + ', however, I don\'t have a matching cloud.'
        )
    # matching_entry = db.session.query(IncomingHostEntry).filter_by(their_address=their_ip).first()
    # if matching_entry is None:
    #     send_unprepared_host_error_and_close(connection)
    #     raise Exception(
    #         'host came asking for cloudname=\'' + cloudname + '\''
    #         + ', but I was not told to expect them.'
    #     )
    # response = recv_msg(connection)
    resp_obj = connection.recv_obj()
    resp_type = resp_obj.type
    # print 'host_host_fetch response:{}'.format(response)
    check_response(HOST_FILE_TRANSFER, resp_type)

    recv_file_tree(resp_obj, matching_cloud, connection, db)
    mylog('[{}]bottom of handle_recv_file(...,{})'
          .format(my_id, msg_obj.__dict__))


def handle_remove_file(connection, address, msg_obj):
    db = get_db()
    my_id = msg_obj.tid
    cloudname = msg_obj.cname
    removed_dir = msg_obj.fpath
    their_ip = address[0]
    resp_type = msg_obj.type
    check_response(REMOVE_FILE, resp_type)

    rd = validate_host_id(db, my_id, connection)
    # validate_host_id will raise an exception if there is no cloud
    matching_id_clouds = rd.data
    matching_cloud = matching_id_clouds.filter_by(name=cloudname).first()
    if matching_cloud is None:
        send_generic_error_and_close(connection)
        raise Exception(
            'host came asking for cloudname=\'' + cloudname + '\''
            + ', however, I don\'t have a matching cloud.'
        )

def filter_func(connection, address):
    # fixme: Failing to decode the message should not bring the entire system down.
    # cont: should gracefully ignore and close connection
    msg_obj = connection.recv_obj()
    mylog('<{}>msg:{}'.format(address, msg_obj.__dict__))
    msg_type = msg_obj.type
    # print 'The message is', msg_obj
    # todo we should make sure the connection was from the remote or a client
    # cont   that we were told about here, before doing ANY processing.

    # NOTE: NEVER REMOTE. NEVER ALLOW REMOTE->HOST.
    try:
        # H->H Messages
        if msg_type == HOST_HOST_FETCH:
            handle_fetch(connection, address, msg_obj)
        elif msg_type == HOST_FILE_PUSH:
            handle_recv_file(connection, address, msg_obj)
        elif msg_type == REMOVE_FILE:
            handle_remove_file(connection, address, msg_obj)
        # ----------------------- C->H Messages ----------------------- #
        # elif msg_type == CLIENT_SESSION_ALERT:
        #     handle_client_session_alert(connection, address, msg_obj)
        elif msg_type == STAT_FILE_REQUEST:
            # todo:2 REALLY? This still isnt here? I guess list files does it...
            pass
        elif msg_type == LIST_FILES_REQUEST:
            list_files_handler(connection, address, msg_obj)
        elif msg_type == CLIENT_FILE_PUT:
            handle_recv_file_from_client(connection, address, msg_obj)
        elif msg_type == READ_FILE_REQUEST:
            handle_read_file_request(connection, address, msg_obj)
        else:
            mylog('I don\'t know what to do with {},\n{}'.format(msg_obj, msg_obj.__dict__))
    except Exception, e:
        sys.stderr.write(e.message + '\n')

    connection.close()

# todo make this work... later
# def filter_func2(connection, address):
#     dont_close = True
#     while dont_close:
#         # keep connection alive and keep processing msgs until reaching an endstate
#         # mostly used for client session type messages
#         msg_obj = recv_msg(connection)
#         msg_type = msg_obj['type']
#         # print 'The message is', msg_obj
#         # todo we should make sure the connection was from the remote or a client
#         # cont   that we were told about here, before doing ANY processing.
#         if msg_type == PREPARE_FOR_FETCH:
#             prepare_for_fetch(connection, address, msg_obj)
#             dont_close = False
#         elif msg_type == HOST_HOST_FETCH:
#             handle_fetch(connection, address, msg_obj)
#             dont_close = False
#         elif msg_type == COME_FETCH:
#             # handle_come_fetch(connection, address, msg_obj)
#             print 'COME_FETCH was a really fucking stupid idea.'
#         elif msg_type == HOST_FILE_PUSH:
#             handle_recv_file(connection, address, msg_obj)
#             dont_close = False
#         elif msg_type == CLIENT_SESSION_ALERT:
#             handle_client_session_alert(connection, address, msg_obj)
#         elif msg_type == STAT_FILE_REQUEST:
#             # fixme
#             pass
#             # handle_recv_file(connection, address, msg_obj)
#         elif msg_type == LIST_FILES_REQUEST:
#             list_files_handler(connection, address, msg_obj)
#         else:
#             print 'I don\'t know what to do with', msg_obj
#             dont_close = False
#     connection.close()


