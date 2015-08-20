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
# fixme this is a dirty hack, I'm sure.
from host import host_db as db
from host import Cloud, FileNode

from datetime import datetime
import time

from stat import *

__author__ = 'Mike'


sys.path.append(os.path.join(sys.path[0], '..'))
# fixme this is a dirty hack, I'm sure.
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
def walktree(top,depth, callback):
    """recursively descend the directory tree rooted at top,
       calling the callback function for each regular file"""

    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        mode = os.stat(pathname).st_mode
        if S_ISDIR(mode):  # It's a directory, recurse into it
            callback(f, depth)
            walktree(pathname,depth+1, callback)
        elif S_ISREG(mode):  # It's a file, call the callback function
            callback(f, depth)
        else:  # Unknown file type, print a message
            print 'Skipping %s' % pathname

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
    sslSocket.write(str(0))  # Host doesn't have an ID yet
    data = sslSocket.recv(1024)
    # print 'Remote responded with a msg-code[', data,']'
    check_response(1, data)
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

    return (0, cloud)


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
    # root_node = FileNode()
    # root_node.name = root
    # file_stat = os.stat(root)
    # mode = file_stat.st_mode
    # curr_modified = file_stat.st_mtime
    # root_node.last_modified = curr_modified
    # root_node.created_on = file_stat.st_ctime
    # db.session.add(root_node)
    cloud.name = cloudname
    # cloud.root_node = root_node
    db.session.commit()


def list_clouds(argv):
    clouds = Cloud.query.all()
    print 'There are ', len(clouds), 'clouds.'
    print '[{}] {:5} {:16} {:24} {:16} {:8}'.format('id'
                                                    , 'my_id'
                                                    , 'name'
                                                    , 'root'
                                                    , 'address'
                                                    , 'port')
    for cloud in clouds:

        print '[{}] {:5} {:16} {:24} {:16} {:8}'\
            .format(cloud.id, cloud.my_id_from_remote, cloud.name
                    , cloud.root_directory
                    , cloud.remote_host, cloud.remote_port)


def db_tree_usage():
    print 'usage: neb tree (-j)(-a)[cloudname]'
    print ''


def tree_usage():
    print 'usage: neb tree (-j)(-a)[cloudname]'
    print ''

def db_tree(argv):
    if len(argv) < 1:
        db_tree_usage()
        return
    print 'tree', argv
    output_json = False
    output_all = False
    cloudname = None
    while len(argv) > 0:
        arg = argv[0]
        args_left = len(argv)
        args_eaten = 0
        if arg == '-j':
            output_json = True
            args_eaten = 1
        if arg == '-a':
            output_all = True
            args_eaten = 1
            raise Exception('tree -a not implemented yet.')
        else:
            cloudname = arg
            args_eaten = 1
        argv = argv[args_eaten:]
    if cloudname is None:
        raise Exception('Must specify a cloud name to mirror')
    match = Cloud.query.filter_by(name=cloudname).first()
    if match is None:
        raise Exception('No cloud on this host with name', cloudname)

    def print_filename(file_node, depth):
        print ('--'*depth) + (file_node.name)

    def walk_db_recursive(file_node, depth, callback):
        callback(file_node, depth)
        for child in file_node.children.all():
            walk_db_recursive(child, depth+1, print_filename)
    for top_level_node in match.files.all():
        walk_db_recursive(top_level_node, 1, print_filename)


def tree(argv):
    if len(argv) < 1:
        tree_usage()
        return
    print 'tree', argv
    output_json = False
    output_all = False
    cloudname = None
    while len(argv) > 0:
        arg = argv[0]
        args_left = len(argv)
        args_eaten = 0
        if arg == '-j':
            output_json = True
            args_eaten = 1
        if arg == '-a':
            output_all = True
            args_eaten = 1
            raise Exception('tree -a not implemented yet.')
        else:
            cloudname = arg
            args_eaten = 1
        argv = argv[args_eaten:]
    if cloudname is None:
        raise Exception('Must specify a cloud name to mirror')
    match = Cloud.query.filter_by(name=cloudname).first()
    if match is None:
        raise Exception('No cloud on this host with name', cloudname)
    root_dir = match.root_directory

    def print_filename(filename, depth):
        print ('--'*depth) + (filename)

    walktree(root_dir, 1, print_filename)


def local_file_create(directory_path, dir_node, filename):
    print '\t\tAdding',filename,'to filenode for',dir_node.name
    file_pathname = os.path.join(directory_path, filename)
    file_stat = os.stat(file_pathname)
    file_modified = file_stat.st_mtime
    file_created = file_stat.st_ctime
    mode = file_stat.st_mode

    filenode = FileNode()
    db.session.add(filenode)
    filenode.name = filename
    filenode.created_on = datetime.fromtimestamp( file_created )
    filenode.last_modified = datetime.fromtimestamp( file_modified )
    dir_node.children.append(filenode)
    db.session.commit()
    print 'total file nodes:', FileNode.query.count()


def local_file_update(directory_path, dir_node, filename, filenode):
    file_pathname = os.path.join(directory_path, filename)
    # pathname = os.path.join(dir_node.name, files[i])
    # todo I think ^this is probably wrong. I think I need the whole path
    # cont and I think I need to build it traversing all the way up...
    # cont OR I could keep it in my DB. Both are bad :/
    file_stat = os.stat(file_pathname)
    file_modified = datetime.fromtimestamp( file_stat.st_mtime)
    mode = file_stat.st_mode
    if file_modified < filenode.last_modified:
        print file_pathname, 'has been modified since we last checked.'
        filenode.last_modified = file_modified
    if S_ISDIR(mode):  # It's a directory, recurse into it
        # use the directory's node as the new root.
        recursive_local_modifications_check(file_pathname, filenode)
        db.session.commit()


def recursive_local_modifications_check (directory_path, dir_node):
    files = sorted(
        os.listdir(directory_path)
        , key=lambda file: file
        , reverse=False
    )
    # print 'dir_node has ', dir_node.children.count(), 'children'

    nodes = dir_node.children.all()
    nodes = sorted(
        nodes
        , key=lambda file: file.name
        , reverse=False
    )
    i = 0
    j = 0
    num_files = len(files)
    num_nodes = len(nodes) if nodes is not None else 0
    # print 'Iterating over (', num_files, num_nodes, '):', files, nodes
    while (i < num_files) and (j < num_nodes):
        # print '\titerating on (file,node)', files[i], nodes[j].name
        if files[i] == nodes[j].name:
            # print '\tfiles were the same'
            local_file_update(directory_path, dir_node, files[i], nodes[j])
            i += 1
            j += 1
        elif files[i] < nodes[j].name:
            # print '\t', files[i], 'was less than', nodes[j].name
            local_file_create(directory_path,dir_node, files[i])
            i += 1
        elif files[i] > nodes[j].name:  # redundant if clause, there for clarity
            # todo handle file deletes, moves.
            j += 1
    while i < num_files: # create the rest of the files
        # print 'finishing', (num_files-i), 'files'
        local_file_create(directory_path, dir_node, files[i])
        i += 1


def check_local_modifications(cloud):
    print 'Checking for modifications on', cloud.name
    root = cloud.root_directory
    # fixme this is a dirty fucking hack
    fake_root_node = FileNode()
    fake_root_node.children = cloud.files
    fake_root_node.name = root
    db.session.add(fake_root_node)
    # print 'started with', [node.name for node in cloud.files.all()]
    # for file in os.listdir(root):
    recursive_local_modifications_check(root, fake_root_node)
    # cloud.files = fake_root_node.children
    all_files = cloud.files
    for child in fake_root_node.children.all():
        if child not in all_files:
            cloud.files.append(child)

    db.session.delete(fake_root_node)
    db.session.commit()
    # print 'ended with',[node.name for node in cloud.files.all()]


def start(argv):
    while True:
        for cloud in Cloud.query.all():
            check_local_modifications(cloud)
        time.sleep(1) # todo: This should be replaced with something
        # cont that actually alerts the process as opposed to just sleep/wake


commands = {
    'mirror': mirror
    # 'new-user': new_user
    , 'start': start
    # , 'create': create
    # , 'list-users': list_users
    , 'list-clouds': list_clouds
    , 'tree': tree
    , 'db_tree': db_tree
}
command_descriptions = {
    'mirror': '\tmirror a remote cloud to this device'
    # 'new-user': '\tadd a new user to the database'
    , 'start': '\t\tstart the main thread checking for updates'
    # , 'create': '\t\tcreate a new cloud to track'
    # , 'list-users': '\tlist all current users'
    , 'list-clouds': '\tlist all current clouds'
    , 'db_tree': '\tdisplays the db structure of a cloud on this host.'
}


def usage(argv):
    print 'usage: neb <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]


if __name__ == '__main__':

    # if there weren't any args, print the usage and return
    if len(sys.argv) < 2:
        usage(sys.argv)
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