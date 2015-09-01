from datetime import datetime
import json
import os
import socket
import ssl
import getpass

from werkzeug.security import generate_password_hash

from host import Cloud
from host import get_db
from host.util import check_response
from msg_codes import *

__author__ = 'Mike'

HOST = 'localhost'
PORT = 12345

def setup_remote_socket(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    # s.create_connection((host, port))
    # TODO May want to use:
    # socket.create_connection(address[, timeout[, source_address]])
    # cont  instead, where address is a (host,port) tuple. It'll try and
    # cont  auto-resolve? which would be dope.
    sslSocket = ssl.wrap_socket(s)
    return sslSocket


def ask_remote_for_id(host, port, db):
    """This performs a code [0] message on the remote host at host:port.
     Awaits a code[1] from the remote.
     Creates a new Cloud for this host:port.
     Returns a (0,cloud.id) if it successfully gets something back.
     """
    sslSocket = setup_remote_socket(host, port)

    # sslSocket.write(str(NEW_HOST_MSG))  # Host doesn't have an ID yet
    # sslSocket.write(make_new_host_json())
    write_msg(make_new_host_json(), sslSocket)

    # data = sslSocket.recv(1024)
    # msg_obj = decode_msg(data)
    msg_obj = recv_msg(sslSocket)

    check_response(ASSIGN_HOST_ID, msg_obj['type'])

    my_id = msg_obj['id']
    print 'Remote says my id is', my_id
    # I have no idea wtf to do with this.
    key = msg_obj['key']
    print 'Remote says my key is', key
    cert = msg_obj['cert']
    print 'Remote says my cert is', cert

    cloud = Cloud()
    cloud.mirrored_on = datetime.utcnow()
    cloud.my_id_from_remote = my_id
    cloud.remote_host = host
    cloud.remote_port = port
    db.session.add(cloud)
    db.session.commit()
    sslSocket.close()
    return (0, cloud)  # returning a status code as well...
    # I've been in kernel land too long, haven't I...


def request_cloud(cloud, db):
    sslSocket = setup_remote_socket(cloud.remote_host, cloud.remote_port)
    username = raw_input('Enter the username for ' + cloud.name + ':').lower()
    print('Enter the password for ' + cloud.name + ':')
    password = getpass.getpass().lower()
    password_hash = generate_password_hash(password)

    write_msg(
        make_request_cloud_json(cloud.my_id_from_remote, cloud.name, username, password_hash)
        , sslSocket
    )

    # msg_obj = decode_msg(sslSocket.recv(1024))
    msg_obj = recv_msg(sslSocket)

    check_response(GO_RETRIEVE_HERE, msg_obj['type'])
    other_address = msg_obj['ip']
    other_port = msg_obj['port']

    if other_address == '0' and other_port == 0:
        print 'No other hosts in cloud'
        sslSocket.close()
        # note: falling out of this function takes us to the code that
        #       sends the MIRRORING_COMPLETE message.
        return

    print 'requesting host at ({},{})'.format(other_address, other_port)

    host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_sock.connect((other_address, other_port))

    # host_sock = setup_remote_socket(other_address, other_port)
    # todo initialize our ssl context here

    send_msg(make_host_host_fetch(cloud.my_id_from_remote, cloud.name, '/'),
             host_sock)
    print 'Sent HOST_HOST_FETCH as a mirror request.'
    # todo Here we need to recv a whole bunch of files from the host
    response = recv_msg(host_sock)
    resp_type = response['type']
    # print 'host_host_fetch response:{}'.format(response)
    check_response(HOST_FILE_TRANSFER, resp_type)
    while response['fsize'] is not None:
        handle_file_transfer(response, cloud, host_sock)
        response = recv_msg(host_sock)


def handle_file_transfer(msg, cloud, socket_conn):
    msg_file_isdir = msg['isdir']
    msg_file_size = msg['fsize']
    msg_rel_path = msg['fpath']
    full_path = os.path.join(cloud.root_directory, msg_rel_path)
    if msg_file_isdir :
        if (not os.path.exists(full_path)):
            os.mkdir(full_path)
            print 'Created directory {}'.format(full_path)
    else:  # is normal file
        data_buffer = ''  # fixme i'm using a string to buffer this?? LOL
        total_read = 0
        while total_read < msg_file_size:
            new_data = socket_conn.recv(min(1024, (msg_file_size-total_read)))  # fixme read only up until end of file
            nbytes = sys.getsizeof(new_data)
            print 'read ({},{})'.format(new_data, nbytes)
            if total_read is None or new_data is None:
                print 'I know I should have broke AND I JUST DIDN\'T ANYWAYS'
                break
            total_read += nbytes
            data_buffer += new_data
            print '<{}>read:{}B, total:{}B, expected total:{}B'.format(
                msg_rel_path, nbytes, total_read, msg_file_size
            )
        print 'complete file data \'{}\''.format(data_buffer)
        file_handle = open(full_path, mode='wb')
        done = False
        total_written = 0
        while not done:
            nbytes_written = file_handle.write(data_buffer[total_written:])
            if nbytes_written is None:
                break
            total_written += nbytes_written
            done = total_written <= 0
        file_handle.close()
        print 'I think I wrote the file to {}'.format(full_path)


def mirror_usage():
    print 'usage: neb mirror [-r address][-p port]' + \
        '[-d root directory][cloudname]'
    print ''


def mirror(argv):
    """
    Things we need for this:
     - [-r address]
     -- The name of the host. Either ip(4/6) or web address?
     -- I think either will work just fine.
     - [cloudname]
     -- The name of a cloud to connect to. We'll figure this out later.
     - [-d root directory]
     -- the path to the root directory that will store this cloud.
     -- default '.'
    """
    db = get_db()
    host = None
    port = PORT
    cloudname = None
    root = '.'
    if len(argv) < 1:
        mirror_usage()
        return
    print 'mirror', argv
    while len(argv) > 0:
        arg = argv[0]
        args_left = len(argv)
        args_eaten = 0
        if arg == '-r':
            if args_left < 2:
                # throw some exception
                raise Exception('not enough args supplied to mirror')
            host = argv[1]
            args_eaten = 2
        elif arg == '-p':
            if args_left < 2:
                # throw some exception
                raise Exception('not enough args supplied to mirror')
            port = argv[1]
            args_eaten = 2
        elif arg == '-d':
            if args_left < 2:
                # throw some exception
                raise Exception('not enough args supplied to mirror')
            root = argv[1]
            args_eaten = 2
        else:
            cloudname = arg
            args_eaten = 1
        argv = argv[args_eaten:]
    # TODO: disallow relative paths. Absolute paths or bust.
    if cloudname is None:
        raise Exception('Must specify a cloud name to mirror')
    if host is None:
        raise Exception('Must specify a host to mirror from')
    print 'attempting to get cloud named \'' + cloudname + '\' from',\
        'host at [',host,'] on port[',port,'], into root [',root,']'
    # okay, so manually decipher the FQDN if they input one.

    (status, cloud) = ask_remote_for_id(host, port, db)
    if not status == 0:
        raise Exception('Exception while mirroring:' +
                        ' could not get ID from remote')

    cloud.root_directory = root
    cloud.name = cloudname
    db.session.commit()
    request_cloud(cloud, db)
    print 'finished requesting cloud'
    new_rem_sock = setup_remote_socket(cloud.remote_host, cloud.remote_port)
    send_msg(
        make_mirroring_complete(cloud.my_id_from_remote, cloud.name)
        , new_rem_sock
    )

    new_rem_sock.close()
    # todo goto code that checks if a nebs.start process is running

    print 'nebs reached bottom of mirror()'

