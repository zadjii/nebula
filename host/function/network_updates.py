from datetime import datetime
import socket
from threading import Thread

from host import get_db, Cloud, IncomingHostEntry, HOST_HOST, HOST_PORT
from host.function.recv_files import recv_file_tree, recv_file_transfer
from host.function.send_files import send_tree
from host.util import check_response, mylog
from msg_codes import *

__author__ = 'Mike'


def receive_updates_thread():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST_HOST, HOST_PORT))
    print 'Listening on ({},{})'.format(HOST_HOST, HOST_PORT)
    s.listen(5)
    while True:
        (connection, address) = s.accept()
        print 'Connected by', address
        thread = Thread(target=filter_func, args=[connection, address])
        thread.start()
        thread.join()
        # todo: possible that we might want to thread.join here.
        # cont  Make it so that each request gets handled before blindly continuing


def prepare_for_fetch(connection, address, msg_obj):
    db = get_db()
    # todo I definitely need to confirm that this is
    # cont   the remote responsible for the cloud
    other_id = msg_obj['id']
    cloudname = msg_obj['cname']
    incoming_address = msg_obj['ip']

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
    print 'Prepared for arrival from', entry.their_address,\
        'looking for cloud', matching_cloud.name


def handle_fetch(connection, address, msg_obj):
    db = get_db()
    other_id = msg_obj['id']
    cloudname = msg_obj['cname']
    requested_root = msg_obj['root']
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
    matching_entry = db.session.query(IncomingHostEntry).filter_by(their_address=their_ip).first()

    # todo: I haven't confirmed their ID yet...
    # cont just that I have a cloud that DOESNT have that id
    if matching_entry is None:
        send_unprepared_host_error_and_close(connection)
        raise Exception(
            'host came asking for cloudname=\'' + cloudname + '\''
            + ', but I was not told to expect them.'
        )

    # connection.send('CONGRATULATIONS! You did it!')
    print 'I SUCCESSFULLY TALKED TO ANOTHER HOST!!!!'

    send_tree(other_id, matching_cloud, requested_root, connection)

def handle_recv_file(connection, address, msg_obj):
    db = get_db()
    my_id = msg_obj['tid']
    cloudname = msg_obj['cname']
    updated_file = msg_obj['fpath']
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
    response = recv_msg(connection)
    resp_type = response['type']
    # print 'host_host_fetch response:{}'.format(response)
    check_response(HOST_FILE_TRANSFER, resp_type)

    recv_file_tree(response, matching_cloud, connection, db)
    mylog('[{}]bottom of handle_recv_file(...,{})'
          .format(my_id, msg_obj))

def filter_func(connection, address):
    msg_obj = recv_msg(connection)
    msg_type = msg_obj['type']
    print 'The message is', msg_obj
    if msg_type == PREPARE_FOR_FETCH:
        prepare_for_fetch(connection, address, msg_obj)
    elif msg_type == HOST_HOST_FETCH:
        handle_fetch(connection, address, msg_obj)
    elif msg_type == COME_FETCH:
        # handle_come_fetch(connection, address, msg_obj)
        print 'COME_FETCH was a really fucking stupid idea.'
    elif msg_type == HOST_FILE_PUSH:
        handle_recv_file(connection, address, msg_obj)
    else:
        print 'I don\'t know what to do with', msg_obj
    connection.close()

