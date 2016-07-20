from datetime import datetime
import socket
import getpass
from sys import stdin
import platform
from werkzeug.security import generate_password_hash
from connections.RawConnection import RawConnection

from host import Cloud, REMOTE_PORT, HOST_PORT, HOST_WS_PORT
from host import get_db
from host.function.recv_files import recv_file_tree
from host.util import check_response, setup_remote_socket, mylog, get_ipv6_list
from messages import *
from msg_codes import *

__author__ = 'Mike'

# FIXME TODO
# Hey there. So I'm looking at this code.
# It looks not super great.
# seems to me like there should be no way to create a Host without also mirroring,
# because this is stupid so yea definitely combine them into one message


def ask_remote_for_id(host, port, db):
    """This performs a code [0] message on the remote host at host:port.
     Awaits a code[1] from the remote.
     Creates a new Cloud for this host:port.
     Returns a (0,cloud.id) if it successfully gets something back.
     """
    sslSocket = setup_remote_socket(host, port)
    raw_conn = RawConnection(sslSocket)
    # write_msg(make_new_host_json(HOST_PORT), sslSocket)
    ipv6_addresses = get_ipv6_list()
    if len(ipv6_addresses) < 1:
        mylog('MY IPV6\'s ARE {}'.format(ipv6_addresses), '31')
        mylog('ERR: could not find an ipv6 address for this host.'
              ' Don\'t really know what to do...')
        return -1, None
    else:
        mylog('\x1b[35m MY IPV6\'s ARE {} \x1b[0m'.format(ipv6_addresses))

    ipv6_addr = ipv6_addresses[0]  # arbitrarily take the first one

    msg = NewHostMessage(ipv6_addr, HOST_PORT, HOST_WS_PORT, platform.uname()[1])
    raw_conn.send_obj(msg)

    resp_obj = raw_conn.recv_obj()
    check_response(ASSIGN_HOST_ID, resp_obj.type)

    my_id = resp_obj.id
    print 'Remote says my id is', my_id
    # I have no idea wtf to do with this.
    key = resp_obj.key
    print 'Remote says my key is', key
    cert = resp_obj.cert
    print 'Remote says my cert is', cert

    sslSocket.close()
    return 0, my_id # returning a status code as well...
    # I've been in kernel land too long, haven't I...


def request_cloud(cloud, test_enabled, db):
    sslSocket = setup_remote_socket(cloud.remote_host, cloud.remote_port)
    if test_enabled:
        print('please enter username for {}:'.format(cloud.name))
        username = stdin.readline()[:-1]
        print('Enter the password for ' + cloud.name + ':')
        password = stdin.readline()[:-1]  # todo this is yea, bad.
    else:
        username = raw_input('Enter the username for ' + cloud.name + ':').lower()
        print('Enter the password for ' + cloud.name + ':')
        password = getpass.getpass()

    raw_conn = RawConnection(sslSocket)
    msg = RequestCloudMessage(cloud.my_id_from_remote, cloud.name, username, password)
    raw_conn.send_obj(msg)

    resp_obj = raw_conn.recv_obj()
    handle_go_retrieve(resp_obj, cloud, db)


def client_request_cloud(cloud, session_id, db):
    sslSocket = setup_remote_socket(cloud.remote_host, cloud.remote_port)
    raw_conn = RawConnection(sslSocket)

    msg = ClientMirrorMessage(session_id, cloud.my_id_from_remote, 'todo_cloud_uname', cloud.name)
    raw_conn.send_obj(msg)

    resp_obj = raw_conn.recv_obj()
    handle_go_retrieve(resp_obj, cloud, db)
    sslSocket.close()


def handle_go_retrieve(response, cloud, db):
    check_response(GO_RETRIEVE_HERE, response.type)
    other_address = response.ip
    other_port = response.port
    other_id = response.id
    if other_address == '0' and other_port == 0:
        print 'No other hosts in cloud'
        # note: falling out of this function takes us to the code that
        #       sends the MIRRORING_COMPLETE message.
        return

    print 'requesting host at [{}]({},{})'.format(other_id, other_address, other_port)

    host_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    host_sock.connect((other_address, other_port, 0, 0))
    host_conn = RawConnection(host_sock)
    # host_sock = setup_remote_socket(other_address, other_port)
    # todo initialize our ssl context here

    # send_msg(make_host_host_fetch(cloud.my_id_from_remote, cloud.name, '/'),
    #          host_sock)
    msg = HostHostFetchMessage(cloud.my_id_from_remote, cloud.name, '/')
    host_conn.send_obj(msg)
    print 'Sent HOST_HOST_FETCH as a mirror request.'

    # Here we recv a whole bunch of files from the host
    # response = recv_msg(host_sock)
    resp_obj = host_conn.recv_obj()
    resp_type = resp_obj.type
    # print 'host_host_fetch response:{}'.format(response)
    check_response(HOST_FILE_TRANSFER, resp_type)
    recv_file_tree(resp_obj, cloud, host_conn, db)


def mirror_usage():
    print 'usage: neb mirror [--test][-r address][-p port]' + \
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
     - [-s session_id]
     -- a string representing a nebula client session_id
     -- if not present, will prompt for a username and password.
    """
    db = get_db()
    host = None
    port = REMOTE_PORT
    cloudname = None
    root = '.'
    test_enabled = False
    session_id = None
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
        elif arg == '-s':
            if args_left < 2:
                # throw some exception
                raise Exception('not enough args supplied to mirror')
            session_id = argv[1]
            args_eaten = 2
        elif arg == '--test':
            test_enabled = True
            args_eaten = 1
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
    # fixme verify that directory is empty, don't do anything if it isn't
    status, my_id = ask_remote_for_id(host, port, db)
    if not status == 0:
        raise Exception('Exception while mirroring:' +
                        ' could not get ID from remote')
    cloud = Cloud()
    cloud.mirrored_on = datetime.utcnow()
    cloud.my_id_from_remote = my_id
    cloud.remote_host = host
    cloud.remote_port = port
    db.session.add(cloud)
    cloud.root_directory = root
    cloud.name = cloudname
    db.session.commit()
    if session_id is None:
        request_cloud(cloud, test_enabled, db)
    else:
        client_request_cloud(cloud, session_id, db)
    mylog('finished requesting cloud')
    new_rem_sock = setup_remote_socket(cloud.remote_host, cloud.remote_port)
    remote_conn = RawConnection(new_rem_sock)
    msg = MirroringCompleteMessage(cloud.my_id_from_remote, cloud.name)
    # send_msg(
    #     make_mirroring_complete(cloud.my_id_from_remote, cloud.name)
    #     , new_rem_sock
    # )
    remote_conn.send_obj(msg)
    cloud.completed_mirroring = True
    db.session.commit()

    new_rem_sock.close()
    # todo goto code that checks if a nebs.start process is running

    mylog('nebs reached bottom of mirror()')

