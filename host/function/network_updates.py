from datetime import datetime
import socket
from threading import Thread

from host import get_db, Cloud, IncomingHostEntry, HOST_HOST, HOST_PORT
from host.function.send_files import send_tree
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

    matching_cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if matching_cloud is None:
        send_generic_error_and_close(connection)
        raise Exception(
            'host came asking for cloudname=\'' + cloudname + '\''
            + ', however, I don\'t have a matching cloud.'
        )
    their_ip = address[0]
    matching_entry = db.session.query(IncomingHostEntry).filter_by(their_address=their_ip).first()
    if matching_entry is None:
        send_unprepared_host_error_and_close(connection)
        raise Exception(
            'host came asking for cloudname=\'' + cloudname + '\''
            + ', but I was not told to expect them.'
        )
    # todo: I haven't confirmed their ID yet...
    # connection.send('CONGRATULATIONS! You did it!')
    print 'I SUCCESSFULLY TALKED TO ANOTHER HOST!!!!'

    send_tree(other_id, matching_cloud, requested_root, connection)


def filter_func(connection, address):
    msg_obj = recv_msg(connection)
    msg_type = msg_obj['type']
    print 'The message is', msg_obj
    if msg_type == PREPARE_FOR_FETCH:
        prepare_for_fetch(connection, address, msg_obj)
    elif msg_type == HOST_HOST_FETCH:
        handle_fetch(connection, address, msg_obj)
    else:
        print 'I don\'t know what to do with', msg_obj
    connection.close()

