import os, sys
from datetime import datetime
import socket
from stat import S_ISDIR
from threading import Thread
from connections.RawConnection import RawConnection

from host import get_db, Cloud, IncomingHostEntry, Session
from host import HOST_HOST, HOST_PORT
from host.function.network.client_session_alert import \
    handle_client_session_alert
from host.function.network.ls_handler import list_files_handler
from host.function.recv_files import recv_file_tree
from host.function.send_files import send_tree
from host.util import check_response, mylog
from messages import ReadFileResponseMessage, FileIsDirErrorMessage, \
    FileDoesNotExistErrorMessage
from msg_codes import *

__author__ = 'Mike'


def receive_updates_thread():
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

    addr_info = socket.getaddrinfo(socket.gethostname(), None)
    mylog('[00]{}'.format(addr_info))
    ipv6_addr = None
    for iface in addr_info:
        if iface[0] == socket.AF_INET6:
            if ipv6_addr is None:
                iface_addr = iface[4]
                mylog('[01]{}'.format(iface_addr))
                if iface_addr[3] == 0:
                    ipv6_addr = iface[4]
    mylog('start on ipv6 address={}'.format(ipv6_addr))
    result = s.bind((ipv6_addr[0], HOST_PORT, 0, 0))
    # s.bind((HOST_HOST, HOST_PORT, 0, 0))
    # mylog('Listening on ({},{})'.format(HOST_HOST, HOST_PORT))
    mylog('Listening on ({},{})'.format(ipv6_addr[0], HOST_PORT))
    mylog('Lets just see:{},{},{} \n{}'.format(s.family, s.type, s.type, result))
    s.listen(5)

    while True:
        (connection, address) = s.accept()
        raw_conn = RawConnection(connection)
        mylog('Connected by {}'.format(address))
        thread = Thread(target=filter_func, args=[raw_conn, address])
        thread.start()
        thread.join()
        # todo: possible that we might want to thread.join here.
        # cont  Make it so that each request gets handled before blindly continuing


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


def handle_recv_file_from_client(connection, address, msg_obj):
    db = get_db()
    # my_id = msg_obj['tid']
    # session_uuid = msg_obj['sid']
    session_uuid = msg_obj.sid
    # cloudname = msg_obj['cname']
    cloudname = msg_obj.cname
    # requested_file = msg_obj['fpath']
    requested_file = msg_obj.fpath
    their_ip = address[0]

    # fixme This is some client session validation. Which obviously needs work.
    # matching_session = db.session.query(Session).filter_by(uuid=session_uuid).first()
    # if matching_session is None:
    #     send_generic_error_and_close(connection)
    #     mylog('ERR: got a CLIENT_._PUT from {} but I don\'t have that session'.format(session_uuid))
    #     # fixme: we should return here, and not actually handle the file....

    # matching_id_clouds = db.session.query(Cloud)\
    #     .filter(Cloud.my_id_from_remote == my_id)
    # if matching_id_clouds.count() <= 0:
    #     send_generic_error_and_close(connection)
    #     raise Exception(
    #         'Received a message intended for id={},'
    #         ' but I don\'t have any clouds with that id'
    #         .format(my_id)
    #     )
    #
    # matching_cloud = matching_session.cloud
    # if matching_cloud is None:
    #     send_generic_error_and_close(connection)
    #     raise Exception(
    #         'The session {} didn\'t have a cloud associated with it'
    #     )
    # fixme make sure that the session has access to the cloud.
    # cont    this will require work from the remote.
    # cont    The client needs to ask the remote for the cloud.
    #           The remote will tell the host (this sid is good for this cname)
    #         the host will add that session to the cloud's list of sessions, and that cloud to the session
    #         the remote will then tell the client to go to that host.

    matching_cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if not (matching_cloud.name == cloudname):
        send_generic_error_and_close(connection)
        raise Exception(
            '{} came asking for cloudname=\'{}\','
            ' however, their cloud doesn\'t match that'
            .format(session_uuid, cloudname)
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
    # resp_type = response['type']
    resp_type = resp_obj.type
    # print 'host_host_fetch response:{}'.format(response)
    check_response(CLIENT_FILE_TRANSFER, resp_type)

    recv_file_tree(resp_obj, matching_cloud, connection, db)
    mylog('[{}]bottom of handle_recv_file_from_client(...,{})'
          .format(session_uuid, msg_obj.__dict__))


def handle_read_file_request(connection, address, msg_obj):
    db = get_db()
    # my_id = msg_obj['tid']
    # session_uuid = msg_obj['sid']
    session_uuid = msg_obj.sid
    # cloudname = msg_obj['cname']
    cloudname = msg_obj.cname
    # requested_file = msg_obj['fpath']
    requested_file = msg_obj.fpath
    their_ip = address[0]
    # todo: refactor this segment out into a verify session function
    # mylog('sessions:{}'.format([(sess.uuid, sess.client_ip) for sess in db.session.query(Session)]))
    # matching_session = db.session.query(Session).filter_by(uuid=session_uuid).first()
    # if matching_session is None:
    #     send_generic_error_and_close(connection)
    #     mylog('ERR: got a RFQ from {} but I don\'t have that session'.format(session_uuid))
    # fixme ^ This all depended upon remotes sending the host a CSA first
    #    which we don't do anymore. so poop on you.

    # matching_id_clouds = db.session.query(Cloud)\
    #     .filter(Cloud.my_id_from_remote == my_id)
    # if matching_id_clouds.count() <= 0:
    #     send_generic_error_and_close(connection)
    #     raise Exception(
    #         'Received a message intended for id={},'
    #         ' but I don\'t have any clouds with that id'
    #         .format(my_id)
    #     )
    #
    # todo: ruh roh, sessions aren't tied to clouds anymore
    # matching_cloud = matching_session.cloud
    # if matching_cloud is None:
    #     send_generic_error_and_close(connection)
    #     raise Exception(
    #         'The session {} didn\'t have a cloud associated with it'
    #     )
    matching_cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    # if not (matching_cloud.name == cloudname):
    #     send_generic_error_and_close(connection)
    #     raise Exception(
    #         '{} came asking for cloudname=\'{}\','
    #         ' however, their cloud doesn\'t match that'
    #             .format(session_uuid, cloudname)
    #     )
    # matching_entry = db.session.query(IncomingHostEntry).filter_by(their_address=their_ip).first()
    # if matching_entry is None:
    #     send_unprepared_host_error_and_close(connection)
    #     raise Exception(
    #         'host came asking for cloudname=\'' + cloudname + '\''
    #         + ', but I was not told to expect them.'
    #     )
    # response = recv_msg(connection)
    # resp_obj = connection.recv_obj()
    # resp_type = response['type']
    # resp_type = resp_obj.type
    # print 'host_host_fetch response:{}'.format(response)
    # check_response(CLIENT_FILE_TRANSFER, resp_type)
    # recv_file_tree(resp_obj, matching_cloud, connection, db)
    requesting_all = requested_file == '/'
    filepath = None
    # if the root is '/', send all of the children of the root
    if requesting_all:
        filepath = matching_cloud.root_directory
    else:
        filepath = os.path.join(matching_cloud.root_directory, requested_file)

    # FIXME: Make sure paths are limited to children of the root

    req_file_stat = None
    try:
        req_file_stat = os.stat(filepath)
    except Exception:
        err_msg = FileDoesNotExistErrorMessage()
        connection.send_obj(err_msg)
        connection.close()
        return
    relative_pathname = os.path.relpath(filepath, matching_cloud.root_directory)

    req_file_is_dir = S_ISDIR(req_file_stat.st_mode)
    if req_file_is_dir:
        err_msg = FileIsDirErrorMessage()
        connection.send_obj(err_msg)
        connection.close()
    else:
        # send RFP - ReadFileResponse
        req_file_size = req_file_stat.st_size
        requested_file = open(filepath, 'rb')
        response = ReadFileResponseMessage(session_uuid, relative_pathname, req_file_size)
        connection.send_obj(response)
        l = 1
        total_len = 0
        # send file bytes
        while l:
            new_data = requested_file.read(1024)
            sent_len = connection.send_next_data(new_data)
            l = sent_len
            total_len += sent_len
            # mylog('sent {}B of <{}> ({}/{}B total)'
            #       .format(sent_len, filepath, total_len, req_file_size))
            # mylog(
            #     '[{}]Sent {}B of file<{}> data'
            #     .format(cloud.my_id_from_remote, l, filepath)
            # )
        mylog(
            '(RFQ)[{}]Sent <{}> data to [{}]'
            .format(matching_cloud.my_id_from_remote, filepath, session_uuid)
        )

        requested_file.close()
    mylog('[{}]bottom of handle_read_file_request(...,{})'
          .format(session_uuid, msg_obj))


def handle_recv_file(connection, address, msg_obj):
    db = get_db()
    # my_id = msg_obj['tid']
    # cloudname = msg_obj['cname']
    # updated_file = msg_obj['fpath']
    my_id = msg_obj.tid
    cloudname = msg_obj.cname
    updated_file = msg_obj.fpath
    their_ip = address[0]

    matching_id_clouds = db.session.query(Cloud)\
        .filter(Cloud.my_id_from_remote == my_id)
    if matching_id_clouds.count() <= 0:
        send_generic_error_and_close(connection)
        raise Exception(
            'Received a message intended for id={},'
            ' but I don\'t have any clouds with that id'
            .format(my_id)
        )

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


def filter_func(connection, address):

    # msg_obj = recv_msg(connection)
    # fixme: Failing to decode the message should not bring the entire system down.
    # cont: should gracefully ignore and close connection
    msg_obj = connection.recv_obj()
    mylog('<{}>msg:{}'.format(address, msg_obj.__dict__))
    msg_type = msg_obj.type
    # print 'The message is', msg_obj
    # todo we should make sure the connection was from the remote or a client
    # cont   that we were told about here, before doing ANY processing.
    try:
        if msg_type == PREPARE_FOR_FETCH:
            prepare_for_fetch(connection, address, msg_obj)
        elif msg_type == HOST_HOST_FETCH:
            handle_fetch(connection, address, msg_obj)
        elif msg_type == HOST_FILE_PUSH:
            handle_recv_file(connection, address, msg_obj)
        elif msg_type == CLIENT_SESSION_ALERT:
            handle_client_session_alert(connection, address, msg_obj)
        elif msg_type == STAT_FILE_REQUEST:
            # fixme
            pass
            # handle_recv_file(connection, address, msg_obj)
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


