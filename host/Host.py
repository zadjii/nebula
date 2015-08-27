from host.function.list_clouds import list_clouds

__author__ = 'Mike'
import os
import socket
import sys
from threading import Thread

from host.function.mirror import mirror
from host.function.tree import db_tree, tree
from msg_codes import *

# from host import host_db as db
from host import Cloud, FileNode, IncomingHostEntry, get_db

from datetime import datetime
import time

from stat import *



###############################################################################
###############################################################################

default_filename = 'C:\\tmp\\touchme.txt'
default_root_path = 'C:/tmp/root-0'

REMOTE_HOST = 'localhost'
REMOTE_PORT = 12345
HOST_HOST = ''
HOST_PORT = 23456

###############################################################################

file_tree_root = {}
modified_files = []


def local_file_create(directory_path, dir_node, filename, db):
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
    if S_ISDIR(mode):  # It's a directory, recurse into it
        # use the directory's node as the new root.
        recursive_local_modifications_check(file_pathname, filenode, db)
        db.session.commit()
    print 'total file nodes:', db.session.query(FileNode).count()


def local_file_update(directory_path, dir_node, filename, filenode, db):
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
        recursive_local_modifications_check(file_pathname, filenode, db)
        db.session.commit()


def recursive_local_modifications_check (directory_path, dir_node, db):
    files = sorted(
        os.listdir(directory_path)
        , key=lambda filename: filename
        , reverse=False
    )
    # print 'dir_node has ', dir_node.children.count(), 'children'

    nodes = dir_node.children.all()
    nodes = sorted(
        nodes
        , key=lambda node: node.name
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
            local_file_update(directory_path, dir_node, files[i], nodes[j], db)
            i += 1
            j += 1
        elif files[i] < nodes[j].name:
            # print '\t', files[i], 'was less than', nodes[j].name
            local_file_create(directory_path,dir_node, files[i], db)
            i += 1
        elif files[i] > nodes[j].name:  # redundant if clause, there for clarity
            # todo handle file deletes, moves.
            j += 1
    while i < num_files:  # create the rest of the files
        # print 'finishing', (num_files-i), 'files'
        local_file_create(directory_path, dir_node, files[i], db)
        i += 1


def check_local_modifications(cloud, db):
    # db = get_db()
    # print 'Checking for modifications on', cloud.name
    root = cloud.root_directory
    # fixme this is a dirty fucking hack
    fake_root_node = FileNode()
    fake_root_node.children = cloud.files
    fake_root_node.name = root
    db.session.add(fake_root_node)
    # print 'started with', [node.name for node in cloud.files.all()]
    # for file in os.listdir(root):
    recursive_local_modifications_check(root, fake_root_node, db)
    # cloud.files = fake_root_node.children
    all_files = cloud.files
    for child in fake_root_node.children.all():
        if child not in all_files:
            cloud.files.append(child)

    db.session.delete(fake_root_node)
    db.session.commit()
    # print 'ended with',[node.name for node in cloud.files.all()]


def local_update_thread():  # todo argv is a placeholder
    db = get_db()
    print 'Beginning to watch for local modifications'
    while True:
        for cloud in db.session.query(Cloud).all():
            check_local_modifications(cloud, db)
        time.sleep(1)  # todo: This should be replaced with something
        # cont that actually alerts the process as opposed to just sleep/wake

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
        send_unprepared_host_error_and_close()
        raise Exception(
            'host came asking for cloudname=\'' + cloudname + '\''
            + ', but I was not told to expect them.'
        )
    # todo: I haven't confirmed their ID yet...
    # connection.send('CONGRATULATIONS! You did it!')
    print 'I SUCCESSFULLY TALKED TO ANOTHER HOST!!!!'
    print 'They requested the file', requested_root
    # find the file on the system, get it's size.
    requesting_all = requested_root == '/'
    filepath = None
    # if the root is '/', send all of the children of the root
    if requesting_all:
        filepath = matching_cloud.root_directory
    else:
        filepath = os.path.join(matching_cloud.root_directory, requested_root)
    print 'The translated request path was {}'.format(filepath)
    send_file_to_other(other_id, matching_cloud, filepath, connection)

    #   open the root path
    # else
    #   open the root dir path + root
    # send a file transfer message
    # while there's file to read: send the file
    # if there are children nodes, send them too

def send_file_to_other(other_id, cloud, filepath, socket_conn):
    """Assumes that the other host was already verified, and the cloud is non-null"""
    req_file_stat = os.stat(filepath)
    relative_pathname = os.path.relpath(filepath, cloud.root_directory)
    print 'relative path for {} in cloud {} is {}'.format(filepath, cloud.name, relative_pathname)
    req_file_is_dir = S_ISDIR(req_file_stat.st_mode)
    if req_file_is_dir:
        send_msg(
            make_host_file_transfer(
                other_id
                , cloud.name
                , relative_pathname
                , req_file_is_dir
                , 0
            )
            , socket_conn
        )
        for f in os.listdir(filepath):
            send_file_to_other(
                other_id
                , cloud
                , os.path.join(filepath, f)
                , socket_conn
            )
    else:
        req_file_size = req_file_stat.st_size
        requested_file = open(filepath, 'rb')
        send_msg(
            make_host_file_transfer(
                other_id
                , cloud.name
                , relative_pathname
                , req_file_is_dir
                , req_file_size
            )
            , socket_conn
        )
        l = 1
        while l:
            new_data = requested_file.read(1024)
            l = socket_conn.send(new_data)
        requested_file.close()


def filter_func(connection, address):
    # inc_data = connection.recv(1024)
    # msg_obj = decode_msg(inc_data)
    msg_obj = recv_msg(connection)
    msg_type = msg_obj['type']
    print 'The message is', msg_obj
    # print 'The message is', msg_obj
    if msg_type == PREPARE_FOR_FETCH:
        prepare_for_fetch(connection, address, msg_obj)
    elif msg_type == HOST_HOST_FETCH:
        handle_fetch(connection, address, msg_obj)
    else:
        print 'I don\'t know what to do with', msg_obj

        # echo_func(connection, address)
    connection.close()
    # try:
    #     print 'The message type is[' + inc_data + ']'
    #     if int(inc_data) == PREPARE_FOR_FETCH:
    #         print 'Handling a PREPARE_FOR_FETCH'
    #         # new_host_handler(connection, address)
    #     elif int(inc_data) == HOST_HOST_FETCH:
    #         handle_fetch(connection, address)
    #         print 'I don\'t know what to do with [', inc_data, ']'
    #         # host_request_cloud(connection, address)
    #     else:
    #         print 'I don\'t know what to do with [', inc_data, ']'
    # except ValueError, e:
    #     json_string = inc_data
    #     msg_obj = json.loads(json_string)
    #     type = msg_obj['type']
    #     if type == HOST_HOST_FETCH:
    #         print 'YEP. Successful json messaging.'
    #     elif type == PREPARE_FOR_FETCH:
    #         other_id = msg_obj['id']
    #         cloudname = msg_obj['name']
    #         incoming_address = msg_obj['name']
    #         matching_cloud = Cloud.query.filter_by(name=cloudname).first()
    #         if matching_cloud is None:
    #             raise Exception(
    #                 'Remote told me to prepare for cloudname=\'' + cloudname + '\''
    #                 + ', however, I don\'t have a matching cloud.'
    #             )
    #         entry = IncomingHostEntry()
    #         entry.their_id_from_remote = other_id
    #         entry.created_on = datetime.utcnow()
    #         entry.their_address = incoming_address
    #         db.session.add(entry)
    #         matching_cloud.incoming_hosts.append(entry)
    #         db.session.commit()
    #         print 'successfully prepared for a host from {}'.format(incoming_address)
    #     # echo_func(connection, address)
    # connection.close()



def start(argv):
    # todo process start() args here
    local_thread = Thread(target=local_update_thread, args=argv)
    network_thread = Thread(target=receive_updates_thread, args=argv)
    local_thread.start()
    network_thread.start()
    # local_thread.join()
    # network_thread.join()
    print 'Both the local update checking thread and the network thread have exited.'


commands = {
    'mirror': mirror
    , 'start': start
    , 'list-clouds': list_clouds
    , 'tree': tree
    , 'db_tree': db_tree
}
command_descriptions = {
    'mirror': '\t\tmirror a remote cloud to this device'
    , 'start': '\t\tstart the main thread checking for updates'
    , 'list-clouds': '\tlist all current clouds'
    , 'tree': '\t\tdisplays the file structure of a cloud on this host.'
    , 'db_tree': '\tdisplays the db structure of a cloud on this host.'
}


def usage(argv):
    print 'usage: nebs <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]

def nebs_main(argv):
    # if there weren't any args, print the usage and return
    if len(argv) < 2:
        usage(argv)
        sys.exit(0)

    command = argv[1]

    selected = commands.get(command, usage)
    selected(argv[2:])
    sys.exit(0)


if __name__ == '__main__':
    nebs_main(sys.argv)

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