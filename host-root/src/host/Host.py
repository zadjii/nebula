import os
import sys
import socket
from threading import Thread
from werkzeug.security import generate_password_hash, \
     check_password_hash
import getpass
from OpenSSL.SSL import SysCallError
from OpenSSL import SSL
import ssl


# print sys.executable
sys.path.append(os.path.join(sys.path[0], '..'))
# todo this is a dirty hack, I'm sure.

from datetime import datetime

from host import host_db as db
# from host import User, Cloud, Host

from stat import *

__author__ = 'Mike'


sys.path.append(os.path.join(sys.path[0], '..'))
# todo this is a dirty hack, I'm sure.
###############################################################################
###############################################################################

default_filename = 'C:\\tmp\\touchme.txt'
default_root_path = 'C:/tmp/root-0'

HOST = 'localhost'
PORT = 12345
###############################################################################

file_tree_root = {}
modified_files = []

# nebs_basedir = os.path.abspath(os.path.dirname(__file__))
# DATABASE_URI = 'sqlite:///' + os.path.join(nebs_basedir, 'nebs.db')

def check_response(expected, recieved):
    if not(int(expected) == int(recieved)):
        raise Exception('Received wrong msg-code, expected',expected,', received',recieved)

def dict_walktree(top, callback, root_struct):
    """recursively descend the directory tree rooted at top,
       calling the callback function for each regular file"""

    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        file_stat = os.stat(pathname)
        mode = file_stat.st_mode
        curr_modified = file_stat.st_mtime
        visiting_node = None

        # first, see if the tree already has a node for this file.
        # if so, check it's mtime, and if modified, add it to the list of updates.
        for node in root_struct['children']:
            if node['path'] == pathname:
                visiting_node = node
                break
        if visiting_node is not None:
            if curr_modified > visiting_node['last_modified']:
                visiting_node['last_modified'] = curr_modified
                modified_files.append(visiting_node)
        # else create a new node.
        else:
            visiting_node = {'last_modified': curr_modified, 'path': pathname, 'children': []}
            root_struct['children'].append(visiting_node)


        if S_ISDIR(mode):  # It's a directory, recurse into it
            # use the directory's node as the new root.
            dict_walktree(pathname, callback, visiting_node)
        elif S_ISREG(mode):  # It's a file, call the callback function
            callback(visiting_node['path'])
        else:  # Unknown file type, print a message
            print 'Skipping %s' % pathname


def visit_file(filename):
    # print 'visiting', filename
    pass


def mirror(argv):
    """
    Things we need for this:
     - [-r address]
     -- The name of the host. Either ip(4/6) or web address?
     -- I think either will work just fine.
     - [cloudname]
     -- The name of a cloud to connect to. We'll figure this out later.
    """
    print 'mirror',argv
    host = None
    port = PORT
    cloudname = None

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
        else:
            cloudname = arg
            args_eaten = 1
        argv = argv[args_eaten:]

    if cloudname is None:
        raise Exception('Must specify a cloud name to mirror')
    print 'attempting to get cloud named \''+cloudname+'\' from',\
        'host at [',host,'] on port[',port,']'
    # okay, so manually decipher the FQDN if they input one.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    # s.create_connection((host, port))
    # May want to use:
    # socket.create_connection(address[, timeout[, source_address]])
    # instead, where address is a (host,port) tuple. It'll try and
    # auto-resolve? which would be dope.
    sslSocket = ssl.wrap_socket(s)
    sslSocket.write(str(0))  # Host doesn't have an ID yet
    data = sslSocket.recv(1024)
    # print 'Remote responded with a msg-code[', data,']'
    check_response(1, data)
    data = sslSocket.recv(1024)
    print 'Remote says my id is', data
    # I have no idea wtf to do with this.
    data = sslSocket.recv(1024)
    print 'Remote says my key is', data
    data = sslSocket.recv(1024)
    print 'Remote says my cert is', data



commands = {
    'mirror':mirror
    # 'new-user': new_user
    # , 'start': start
    # , 'create': create
    # , 'list-users': list_users
    # , 'list-clouds': list_clouds
}
command_descriptions = {
    'mirror':'\tmirror a remote cloud to this device'
    # 'new-user': '\tadd a new user to the database'
    # , 'start': '\t\tstart the remote server'
    # , 'create': '\t\tcreate a new cloud to track'
    # , 'list-users': '\tlist all current users'
    # , 'list-clouds': '\tlist all current clouds'
}


def usage():
    print 'usage: neb <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]



if __name__ == '__main__':

    # if there weren't any args, print the usage and return
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)

    command = sys.argv[1]

    selected = commands.get(command, usage)
    selected(sys.argv[2:])
    sys.exit(0)
#
#
# if __name__ == '__main__':
#     root_path = sys.argv[1] if len(sys.argv) > 1 else default_root_path
#
#     last_modified = os.stat(default_filename).st_mtime
#
#     print last_modified
#
#     file_tree_root['last_modified'] = last_modified
#     file_tree_root['path'] = root_path
#     file_tree_root['children'] = []
#
#     while True:
#         modified_files = []
#         dict_walktree(root_path, visit_file, file_tree_root)
#         if len(modified_files) > 0:
#             print str(len(modified_files)) + ' file(s) were modified.'
#         # now_modified = os.stat(default_filename).st_mtime
#         # if now_modified > last_modified:
#         #     print default_filename, ' was modified at ', now_modified, ', last ', last_modified
#         #     last_modified = now_modified
#             # This socket can either be AF_INET for v4 or AF_INET6 for v6
#             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             s.connect((HOST, PORT))
#             # May want to use:
#             # socket.create_connection(address[, timeout[, source_address]])
#             # instead, where address is a (host,port) tuple. It'll try and
#             # auto-resolve? which would be dope.
#             sslSocket = ssl.wrap_socket(s)
#             sslSocket.write(str(-1))  # placeholder message type
#             num_sent = 0
#             for file_node in modified_files:
#                 sslSocket.write(file_node['path'] + ' was modified at ' + str(file_node['last_modified']))
#                 num_sent += 1
#             # sslSocket.write(default_filename + ' was modified at ' + str(now_modified))
#             pulling = True
#             num_recvd = 0
#             while pulling and (num_recvd < num_sent):
#                 data = sslSocket.recv(1024)
#                 if not data:
#                     pulling = False
#                 print 'remote responded['+str(len(data))+']: ' + repr(data)
#                 num_recvd += 1
#             # sslSocket.unwrap()
#             # sslSocket.close()
#             s.shutdown(socket.SHUT_RDWR)
#             s.close()
#         else:
#             print 'No updates'
#         time.sleep(1)
#
#     # s.connect((HOST, PORT))
#     #
#     # sslSocket = ssl.wrap_socket(s)
#     #
#     # sslSocket.write('Hello secure socket\n')
#     # data = sslSocket.recv(4096)
#     # print repr(data)
#     # s.close()