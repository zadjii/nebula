from datetime import datetime
import os
import socket
from stat import S_ISDIR
import time
from connections.RawConnection import RawConnection
from host import FileNode, get_db, Cloud, HOST_PORT
from host.function.send_files import send_file_to_other, complete_sending_files
from host.util import check_response, setup_remote_socket, mylog, get_ipv6_list
from msg_codes import *
from messages import *

__author__ = 'Mike'


def send_updates(cloud, updates):
    mylog('[{}] has updates {}'.format(cloud.my_id_from_remote, updates))
    # connect to remote
    ssl_sock = setup_remote_socket(cloud.remote_host, cloud.remote_port)
    raw_connection = RawConnection(ssl_sock)
    # get hosts list
    msg = GetActiveHostsRequestMessage(cloud.my_id_from_remote, cloud.name)
    raw_connection.send_obj(msg)
    response = raw_connection.recv_obj()
    check_response(GET_ACTIVE_HOSTS_RESPONSE, response.type)
    hosts = response.hosts
    updated_peers = 0
    for host in hosts:
        if host['id'] == cloud.my_id_from_remote:
            continue
        update_peer(cloud, host, updates)
        updated_peers += 1
    mylog('[{}] updated {} peers'.format(cloud.my_id_from_remote, updated_peers))


def update_peer(cloud, host, updates):
    host_id = host['id']
    host_ip = host['ip']
    host_port = host['port']
    host_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    host_sock.connect((host_ip, host_port, 0, 0))
    raw_connection = RawConnection(host_sock)
    msg = HostFilePushMessage(host_id, cloud.name, 'i-dont-give-a-fuck')
    raw_connection.send_obj(msg)

    for update in updates:
        file_path = update[1]
        relative_pathname = os.path.relpath(file_path, cloud.root_directory)
        if update[0] == FILE_CREATE or update[0] == FILE_UPDATE:
            send_file_to_other(
                host_id
                , cloud
                , os.path.join(cloud.root_directory, relative_pathname)
                , raw_connection
                , recurse=False)
        elif update[0] == FILE_DELETE:
            msg = RemoveFileMessage(host_id, cloud.name, relative_pathname)
            raw_connection.send_obj(msg)
        else:
            print 'Welp this shouldn\'t happen'
    complete_sending_files(host_id, cloud, None, raw_connection)


def local_file_create(host_obj, directory_path, dir_node, filename, db):
    # print '\t\tAdding',filename,'to filenode for',dir_node.name
    file_pathname = os.path.join(directory_path, filename)
    file_stat = os.stat(file_pathname)
    file_modified = file_stat.st_mtime
    file_created = file_stat.st_ctime
    mode = file_stat.st_mode

    filenode = FileNode()
    db.session.add(filenode)
    filenode.name = filename
    filenode.created_on = datetime.utcfromtimestamp( file_created )
    filenode.last_modified = datetime.utcfromtimestamp( file_modified )
    try:
        filenode.cloud = dir_node.cloud
    except AttributeError:
        filenode.cloud = dir_node
    dir_node.children.append(filenode)
    db.session.commit()

    # Theoretically, the private data should have already been loaded or
    # created. I guess the first time that the private data is generated, this
    # happens. Might actually cause the host to write the .nebs, then read it
    # right back in.
    # Not really the worst.
    if host_obj.is_private_data_file(file_pathname, filenode.cloud):
        host_obj.reload_private_data(filenode.cloud)

    updates = [(FILE_CREATE, file_pathname)]
    if S_ISDIR(mode):  # It's a directory, recurse into it
        # use the directory's node as the new root.
        rec_updates = recursive_local_modifications_check(host_obj,
                                                          file_pathname,
                                                          filenode,
                                                          db)
        updates.extend(rec_updates)
        db.session.commit()
    return updates


def local_file_update(host_obj, directory_path, dir_node, filename, filenode, db):
    file_pathname = os.path.join(directory_path, filename)
    file_stat = os.stat(file_pathname)
    file_modified = datetime.utcfromtimestamp( file_stat.st_mtime)
    mode = file_stat.st_mode
    updates = []
    # mylog('[{}]\n\t{}\n\t{}'
    #       .format(filenode.id, file_modified, filenode.last_modified))
    # todo at least on Windows: doesn't account for the timezone when I'm using
    # cont   UTC times. Probably *nix as well. Need to convert them to UTC.
    # todo Should also store the current UTC offset when we notice a change.
    # cont   and use that, because computers move around.
    # note I fucking hate timezones.
    delta = file_modified - filenode.last_modified
    if file_modified > filenode.last_modified:
        filenode.last_modified = file_modified
        db.session.commit()
        updates.append((FILE_UPDATE, file_pathname))
        if host_obj.is_private_data_file(file_pathname, filenode.cloud):
            host_obj.reload_private_data(filenode.cloud)

        # else:
        # mylog('[{}]<{}> wasnt updated'.format(filenode.id, file_pathname))
    if S_ISDIR(mode):  # It's a directory, recurse into it
        # use the directory's node as the new root.
        rec_updates = recursive_local_modifications_check(host_obj, file_pathname, filenode, db)
        db.session.commit()
        updates.extend(rec_updates)
    return updates


FILE_CREATE = 0
FILE_UPDATE = 1
FILE_DELETE = 2


def recursive_local_modifications_check(host_obj, directory_path, dir_node, db):
    files = sorted(os.listdir(directory_path), key=lambda filename: filename, reverse=False)
    nodes = dir_node.children.all()
    nodes = sorted(nodes, key=lambda node: node.name, reverse=False)

    i = j = 0
    num_files = len(files)
    num_nodes = len(nodes) if nodes is not None else 0
    original_total_nodes = db.session.query(FileNode).count()
    updates = []
    while (i < num_files) and (j < num_nodes):
        if files[i] == nodes[j].name:
            update_updates = local_file_update(host_obj, directory_path, dir_node, files[i], nodes[j], db)
            updates.extend(update_updates)
            i += 1
            j += 1
        elif files[i] < nodes[j].name:
            create_updates = local_file_create(host_obj, directory_path, dir_node, files[i], db)
            updates.extend(create_updates)
            i += 1
        elif files[i] > nodes[j].name:  # redundant if clause, there for clarity
            # todo handle file deletes, moves.
            # updates.append((FILE_DELETE, nodes[j])) -> this is a problemo
            j += 1
    while i < num_files:  # create the rest of the files
        # print 'finishing', (num_files-i), 'files'
        create_updates = local_file_create(host_obj, directory_path, dir_node, files[i], db)
        updates.extend(create_updates)
        i += 1
    # todo handle j < num_nodes, bulk end deletes
    new_num_nodes = db.session.query(FileNode).count()
    # if not new_num_nodes == original_total_nodes:
    #     mylog('RLM:total file nodes:{}'.format(new_num_nodes))

    return updates


def check_local_modifications(host_obj, cloud, db):
    root = cloud.root_directory
    updates = recursive_local_modifications_check(host_obj, root, cloud, db)
    if len(updates) > 0:
        send_updates(cloud, updates)


def check_ipv6_changed(curr_ipv6):
    ipv6_addresses = get_ipv6_list()
    if curr_ipv6 is None:
        if len(ipv6_addresses) > 0:
            return True, ipv6_addresses[0]
        else:
            return False, None
    if curr_ipv6 in ipv6_addresses:
        return False, None
    else:
        new_addr = None
        if len(ipv6_addresses) > 1:
            new_addr = ipv6_addresses[0]
        return True, new_addr


def local_update_thread(host_obj):
    db = get_db()
    print 'Beginning to watch for local modifications'
    mirrored_clouds = db.session.query(Cloud).filter_by(completed_mirroring=True)
    num_clouds_mirrored = 0  # mirrored_clouds.count()

    current_ipv6 = host_obj.active_ipv6()
    host_obj.handshake_clouds(mirrored_clouds.all())
    # for cloud in mirrored_clouds.all():
    #     host_obj.send_remote_handshake(cloud)
    last_handshake = datetime.utcnow()
    db.session.close()
    while not host_obj.is_shutdown_requested():
        # process all of the incoming requests first
        host_obj.process_connections()

        db = get_db()
        mirrored_clouds = db.session.query(Cloud).filter_by(completed_mirroring=True)
        all_mirrored_clouds = mirrored_clouds.all()

        # check if out ip has changed since last update
        ip_changed, new_ip = False, None
        if host_obj.is_ipv6():
            ip_changed, new_ip = check_ipv6_changed(current_ipv6)

        # if the ip is different, move our server over
        if ip_changed:
            host_obj.change_ip(new_ip, all_mirrored_clouds)
            # todo: what if one of the remotes fails to handshake?
            # should store the last handshake per remote
            last_handshake = datetime.utcnow()
            current_ipv6 = new_ip

        # if the number of mirrors has changed...
        if num_clouds_mirrored < mirrored_clouds.count():
            mylog('checking for updates on {}'.format([cloud.my_id_from_remote for cloud in all_mirrored_clouds]))
            num_clouds_mirrored = mirrored_clouds.count()
            # if the number of clouds is different:
            # - handshake all of them
            # - Load the private data for any new ones into memory
            for cloud in all_mirrored_clouds:
                # load_private_data doesn't duplicate existing data
                host_obj.load_private_data(cloud)
                host_obj.send_remote_handshake(cloud)

            last_handshake = datetime.utcnow()

        # scan the tree for updates
        for cloud in all_mirrored_clouds:
            check_local_modifications(host_obj, cloud, db)

        # if more that 30s have passed since the last handshake, handshake
        delta = datetime.utcnow() - last_handshake
        if delta.seconds > 30:
            host_obj.handshake_clouds(all_mirrored_clouds)
            # for cloud in all_mirrored_clouds:
            #     host_obj.send_remote_handshake(cloud)
            last_handshake = datetime.utcnow()
        db.session.close()
        time.sleep(1)  # todo: This should be replaced with something
        # cont that actually alerts the process as opposed to just sleep/wake

