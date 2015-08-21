from datetime import datetime
import socket
import ssl
import getpass
from werkzeug.security import generate_password_hash

from host import Cloud
from host import host_db as db
from host.util import check_response
from host.msg_codes import *

__author__ = 'Mike'

HOST = 'localhost'
PORT = 12345

def setup_remote_socket(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    # s.create_connection((host, port))
    # May want to use:
    # socket.create_connection(address[, timeout[, source_address]])
    # instead, where address is a (host,port) tuple. It'll try and
    # auto-resolve? which would be dope.
    sslSocket = ssl.wrap_socket(s)
    return sslSocket


def ask_remote_for_id(host, port):
    """This performs a code [0] message on the remote host at host:port.
     Awaits a code[1] from the remote.
     Creates a new Cloud for this host:port.
     Returns a (0,cloud.id) if it successfully gets something back.
     """
    sslSocket = setup_remote_socket(host,port)
    sslSocket.write(str(NEW_HOST_MSG))  # Host doesn't have an ID yet
    data = sslSocket.recv(1024)
    # print 'Remote responded with a msg-code[', data,']'
    check_response(ASSIGN_HOST_ID, data)
    my_id = sslSocket.recv(1024)
    print 'Remote says my id is', my_id
    # I have no idea wtf to do with this.
    data = sslSocket.recv(1024)
    print 'Remote says my key is', data
    data = sslSocket.recv(1024)
    print 'Remote says my cert is', data
    cloud = Cloud()
    cloud.mirrored_on = datetime.utcnow()
    cloud.my_id_from_remote = my_id
    cloud.remote_host = host
    cloud.remote_port = port
    db.session.add(cloud)
    db.session.commit()

    return (0, cloud)  # returning a status code as well...
    # I've been in kernel land too long, haven't I...


def request_cloud(cloud):
    sslSocket = setup_remote_socket(cloud.remote_host, cloud.remote_port)
    username = raw_input('Enter the username for ' + cloud.name + ':').lower()
    password = getpass.getpass('Enter the password for ' + cloud.name + ':').lower()
    password_hash = generate_password_hash(password)

    sslSocket.write(str(REQUEST_CLOUD))
    sslSocket.write(str(cloud.my_id_from_remote))
    sslSocket.write(str(len(cloud.name)))
    sslSocket.write(str(cloud.name))
    sslSocket.write(username)
    sslSocket.write(password_hash)

    other_address = sslSocket.recv(1024)
    other_port = sslSocket.recv(1024)

    if other_address == '0' and other_port == '0':
        print 'No other hosts in cloud'
        return

    host_sock = setup_remote_socket(other_address, other_port)
    host_sock.write(str(HOST_HOST_FETCH))
    host_sock.write(cloud.name)
    host_sock.write('/')



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
    print 'attempting to get cloud named \''+cloudname+'\' from',\
        'host at [',host,'] on port[',port,'], into root [',root,']'
    # okay, so manually decipher the FQDN if they input one.

    (status, cloud) = ask_remote_for_id(host, port)
    if not status == 0:
        raise Exception('Exception while mirroring:' +
                        ' could not get ID from remote')

    cloud.root_directory = root
    cloud.name = cloudname
    db.session.commit()
    request_cloud(cloud)

