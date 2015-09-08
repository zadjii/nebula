from datetime import datetime
import os
import socket
from stat import S_ISDIR
import time
from host import FileNode, get_db, Cloud, HOST_PORT
from host.function.send_files import send_file_to_other, complete_sending_files
from host.util import check_response, setup_remote_socket, mylog
from msg_codes import *

__author__ = 'Mike'

def send_updates(cloud, updates, db):
    mylog('[{}] has updates {}'.format(cloud.my_id_from_remote, updates))
    # connect to remote
    ssl_sock = setup_remote_socket(cloud.remote_host, cloud.remote_port)
    # get hosts list
    send_msg(make_get_hosts_request(cloud.my_id_from_remote, cloud.name), ssl_sock)
    response = recv_msg(ssl_sock)
    check_response(GET_HOSTS_RESPONSE, response['type'])
    hosts = response['hosts']
    updated_peers = 0
    for host in hosts:
        if host['id'] == cloud.my_id_from_remote:
            continue
        update_peer(cloud, host, updates)
        updated_peers += 1
    print '[{}] updated {} peers'.format(cloud.my_id_from_remote, updated_peers)


def update_peer(cloud, host, updates):
    host_id = host['id']
    host_ip = host['ip']
    host_port = host['port']
    host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_sock.connect((host_ip, host_port))
    send_msg(make_host_file_push(host_id, cloud.name, 'i-dont-give-a-fuck'), host_sock)
    for update in updates:
        file_path = update[1]
        relative_pathname = os.path.relpath(file_path, cloud.root_directory)
        # mylog('translated path \'{}\'-\'{}\'=?\'{}\''.format(file_path, cloud.root_directory, relative_pathname))
        if update[0] == FILE_CREATE or update[0] == FILE_UPDATE:
            send_file_to_other(
                host_id
                , cloud
                , os.path.join(cloud.root_directory, relative_pathname)
                , host_sock)
        elif update[0] == FILE_DELETE:
            send_msg(make_remove_file(host_id, cloud.name, relative_pathname), host_sock)
        else:
            print 'Welp this shouldn\'t happen'
    complete_sending_files(host_id, cloud, None, host_sock)


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
    updates = [(FILE_CREATE, file_pathname)]
    if S_ISDIR(mode):  # It's a directory, recurse into it
        # use the directory's node as the new root.
        rec_updates = recursive_local_modifications_check(file_pathname, filenode, db)
        updates.extend(rec_updates)
        db.session.commit()
    return updates


def local_file_update(directory_path, dir_node, filename, filenode, db):
    file_pathname = os.path.join(directory_path, filename)
    # pathname = os.path.join(dir_node.name, files[i])
    # todo I think ^this is probably wrong. I think I need the whole path
    # cont and I think I need to build it traversing all the way up...
    # cont OR I could keep it in my DB. Both are bad :/
    file_stat = os.stat(file_pathname)
    file_modified = datetime.fromtimestamp( file_stat.st_mtime)
    mode = file_stat.st_mode
    updates = []
    if file_modified > filenode.last_modified:
        mylog('<{}>:[<{}>,{}] has been modified,\n\t  {}\n\t> {}[{:4},{:4}]'
              .format(file_pathname
                      , dir_node.name
                      , dir_node.id
                      , file_modified
                      , filenode.last_modified
                      , filenode.parent_id
                      , filenode.cloud_id
                      ))
        filenode.last_modified = file_modified
        updates.append((FILE_UPDATE, file_pathname))
    if S_ISDIR(mode):  # It's a directory, recurse into it
        # use the directory's node as the new root.
        rec_updates = recursive_local_modifications_check(file_pathname, filenode, db)
        db.session.commit()
        updates.extend(rec_updates)
    return updates


FILE_CREATE = 0
FILE_UPDATE = 1
FILE_DELETE = 2

def recursive_local_modifications_check(directory_path, dir_node, db):
    mylog('RLM [{:3}]'.format(dir_node.id))
    files = sorted(os.listdir(directory_path), key=lambda filename: filename, reverse=False)
    nodes = dir_node.children.all()
    nodes = sorted(nodes, key=lambda node: node.name, reverse=False)
    mylog('\t_rlm_{}'.format([node.name for node in nodes]))
    i = j = 0
    num_files = len(files)
    num_nodes = len(nodes) if nodes is not None else 0
    original_total_nodes = db.session.query(FileNode).count()
    updates = []
    # print 'Iterating over (', num_files, num_nodes, '):', files, nodes
    while (i < num_files) and (j < num_nodes):
        # print '\titerating on (file,node)', files[i], nodes[j].name
        if files[i] == nodes[j].name:
            # print '\tfiles were the same'
            update_updates = local_file_update(directory_path, dir_node, files[i], nodes[j], db)
            # updates.append((FILE_UPDATE, files[i]))
            updates.extend(update_updates)
            i += 1
            j += 1
        elif files[i] < nodes[j].name:
            # print '\t', files[i], 'was less than', nodes[j].name
            create_updates = local_file_create(directory_path, dir_node, files[i], db)
            updates.extend(create_updates)
            # updates.append((FILE_CREATE, files[i]))
            i += 1
        elif files[i] > nodes[j].name:  # redundant if clause, there for clarity
            # todo handle file deletes, moves.
            # updates.append((FILE_DELETE, nodes[j])) -> this is a problemo
            j += 1
    while i < num_files:  # create the rest of the files
        # print 'finishing', (num_files-i), 'files'
        create_updates = local_file_create(directory_path, dir_node, files[i], db)
        updates.extend(create_updates)
        # updates.append((FILE_CREATE, files[i]))
        i += 1
    # todo handle j < num_nodes, bulk end deletes
    new_num_nodes = db.session.query(FileNode).count()
    if not new_num_nodes == original_total_nodes:
        print 'RLM:total file nodes:', new_num_nodes

    return updates


def check_local_modifications(cloud, db):
    # db = get_db()
    # print 'Checking for modifications on', cloud.name
    root = cloud.root_directory
    ##########
    # fixme this is a dirty fucking hack
    # fake_root_node = FileNode()
    # fake_root_node.children = cloud.files
    # fake_root_node.name = root
    # db.session.add(fake_root_node)
    # # print 'started with', [node.name for node in cloud.files.all()]
    # # for file in os.listdir(root):
    # mylog('clm {}-{}-[{}]-{}'.format(fake_root_node, fake_root_node.children, cloud.my_id_from_remote, [(node.id, node.name) for node in fake_root_node.children]))
    # updates = recursive_local_modifications_check(root, fake_root_node, db)
    # # print 'updates={}'.format(updates)
    # if len(updates) > 0:
    #     send_updates(cloud, updates, db)
    #
    # # cloud.files = fake_root_node.children
    # all_files = cloud.files
    # for child in fake_root_node.children.all():
    #     if child not in all_files:
    #         cloud.files.append(child)
    #         child.parent_id = None
    #         mylog('\t\tadded <{}> to [{}]'.format(child.name, cloud.my_id_from_remote))
    # # fake_root_node.children[:] = []
    # db.session.delete(fake_root_node)
    # db.session.commit()
    ###########
    updates = recursive_local_modifications_check(root, cloud, db)
    if len(updates) > 0:
        send_updates(cloud, updates, db)

    # print 'ended with',[node.name for node in cloud.files.all()]
    # todo send updates
    # cont Any time a file is updated or a node created, append to a list
    # cont   of updates.
    # cont Get all of the hosts from the remote.
    # cont For each host, we send all of those update/create/deletes out
    # cont We COULD be super contrived here, and just send a COME_FETCH msg,
    # cont   that tells them to fetch the file from us instead of pushing the
    # cont   file. Puts the work on the network thread.
    # cont   Eh, for ease, that's how we'll do it.

def local_update_thread():  # todo argv is a placeholder
    db = get_db()
    print 'Beginning to watch for local modifications'
    mirrored_clouds = db.session.query(Cloud).filter_by(completed_mirroring=True)
    num_clouds_mirrored = 0  # mirrored_clouds.count()
    while True:
        all_mirrored_clouds = mirrored_clouds.all()
        if num_clouds_mirrored < mirrored_clouds.count():
            mylog('checking for updates on {}'.format([cloud.my_id_from_remote for cloud in all_mirrored_clouds]))
            num_clouds_mirrored = mirrored_clouds.count()
        for cloud in all_mirrored_clouds:
            check_local_modifications(cloud, db)
        time.sleep(1)  # todo: This should be replaced with something
        # cont that actually alerts the process as opposed to just sleep/wake


