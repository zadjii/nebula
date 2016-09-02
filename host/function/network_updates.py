import sys
from datetime import datetime

from host import get_db, Cloud, IncomingHostEntry
from host.function.network.client import handle_recv_file_from_client, \
    handle_read_file_request, list_files_handler
# from host.function.network.ls_handler import list_files_handler
from host.function.recv_files import recv_file_tree
from host.function.send_files import send_tree
from host.util import check_response, mylog, validate_host_id
from msg_codes import *

__author__ = 'Mike'


def prepare_for_fetch(connection, address, msg_obj):
    db = get_db()
    # todo I definitely need to confirm that this is
    # cont   the remote responsible for the cloud
    other_id = msg_obj.id
    cloudname = msg_obj.cname
    incoming_address = msg_obj.ip

    matching_cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if matching_cloud is None:
        raise Exception(
            'Remote told me to prepare for cloudname=\'' + cloudname + '\''
            + ', however, I don\'t have a matching cloud.'
        )
    entry = IncomingHostEntry()
    entry.their_id_from_remote = other_id
    entry.created_on = datetime.utcnow()
    entry.their_address = incoming_address
    db.session.add(entry)
    matching_cloud.incoming_hosts.append(entry)
    db.session.commit()
    mylog('Prepared for arrival from {} looking for cloud "{}"'.format(
        entry.their_address, matching_cloud.name
    ))


def handle_fetch(connection, address, msg_obj):
    db = get_db()
    other_id = msg_obj.id
    cloudname = msg_obj.cname
    requested_root = msg_obj.root

    # fuck this is super wrong. fixme.
    # validate host id gets it's clouds, but we don't want that.
    # rd = validate_host_id(db, other_id, connection)
    # validate_host_id will raise an exception if there is no cloud
    # matching_id_clouds = rd.data

    # fixme just temporarily re-enabling the old codepath until I figure this out.
    matching_id_clouds = db.session.query(Cloud)\
        .filter(Cloud.my_id_from_remote != other_id)\
        .filter_by(completed_mirroring=True)
    if matching_id_clouds.count() <= 0:
        send_generic_error_and_close(connection)
        raise Exception(
            'Received a message intended from id={},'
            ' but I don\'t have any clouds with that DON\'T have that id'
            .format(other_id)
        )

    matching_cloud = matching_id_clouds.filter_by(name=cloudname).first()
    if matching_cloud is None:
        send_generic_error_and_close(connection)
        raise Exception(
            'host came asking for cloudname=\'' + cloudname + '\''
            + ', however, I don\'t have a matching cloud.'
        )
    their_ip = address[0]
    mylog('skipping IncomingHost authorization in handle_fetch')
    mylog('The connected host is via IP="{}"'.format(their_ip))
    # matching_entry = db.session.query(IncomingHostEntry).filter_by(their_address=their_ip).first()
    #
    # # todo: I haven't confirmed their ID yet...
    # # cont just that I have a cloud that DOESNT have that id
    # if matching_entry is None:
    #     send_unprepared_host_error_and_close(connection)
    #     raise Exception(
    #         'host came asking for cloudname=\'' + cloudname + '\''
    #         + ', but I was not told to expect them.'
    #     )

    # connection.send('CONGRATULATIONS! You did it!')
    print 'I SUCCESSFULLY TALKED TO ANOTHER HOST!!!!'

    send_tree(other_id, matching_cloud, requested_root, connection)


def handle_recv_file(connection, address, msg_obj):
    db = get_db()
    # my_id = msg_obj['tid']
    # cloudname = msg_obj['cname']
    # updated_file = msg_obj['fpath']
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
        if msg_type == PREPARE_FOR_FETCH:
            # todo:14 remove. This is a R->H message.
            prepare_for_fetch(connection, address, msg_obj)
        # H->H Messages
        elif msg_type == HOST_HOST_FETCH:
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


