from datetime import datetime
import os
import socket
from stat import S_ISDIR
import time

from common.SimpleDB import SimpleDB
from connections.RawConnection import RawConnection
from host.HostController import HostController
from host.models.FileNode import FileNode
from host.models.Cloud import Cloud
from host.function.network_updates import handle_remove_file
from host.function.send_files import send_file_to_other, complete_sending_files, send_file_to_local
from common_util import *
from host.util import check_response, setup_remote_socket, get_ipv6_list, find_deletable_children
from msg_codes import *
from messages import *

__author__ = 'Mike'


def send_updates(host_obj, db, cloud, updates):
    _log = get_mylog()
    _log.info('[{}] has updates {}'.format(cloud.my_id_from_remote, updates))
    # connect to remote

    rd = setup_remote_socket(cloud)
    if not rd.success:
        msg = 'Failed to connect to remote: {}'.format(rd.data)
        _log.error(msg)
        # TODO: At this point, the local updates will not be reflected in the
        #   nebula. This is a spot to come back to when we add support for
        #   multiple hosts.
        return
    remote_sock = rd.data
    raw_connection = RawConnection(remote_sock)
    # get hosts list
    msg = GetActiveHostsRequestMessage(cloud.my_id_from_remote, cloud.uname(), cloud.cname())
    raw_connection.send_obj(msg)
    response = raw_connection.recv_obj()
    check_response(GET_ACTIVE_HOSTS_RESPONSE, response.type)
    hosts = response.hosts
    updated_peers = 0
    for host in hosts:
        if host['id'] == cloud.my_id_from_remote:
            continue
        update_peer(host_obj, db, cloud, host, updates)
        updated_peers += 1
    _log.info('[{}] updated {} peers'.format(cloud.my_id_from_remote, updated_peers))


def update_peer(host_obj, db, cloud, host, updates):
    host_id = host['id']  # id of host to recv files
    host_ip = host['ip']
    host_port = host['port']

    is_ipv6 = ':' in host_ip
    sock_type = socket.AF_INET6 if is_ipv6 else socket.AF_INET
    sock_addr = (host_ip, host_port, 0, 0) if is_ipv6 else (host_ip, host_port)

    host_sock = socket.socket(sock_type, socket.SOCK_STREAM)
    host_sock.connect(sock_addr)

    # TODO If this connect fails, We're just gonna crash.
    # File under the list of try/excepts around connecting.
    # also todo: re multiple hosts. all kinda related here.
    # Also, what if we're currently offline? We probably didn't even get this far...
    # todo: hosts should encrypt to one another, yea?
    # Todo: how do hosts validate each other's identity?

    raw_connection = RawConnection(host_sock)

    # fixme: Change it to one FILE_PUSH per update. (note have I already done this?)
    # First check if the peer is local or not,
    #   then either send_updates_other or send_updates_local
    #   send_updates_other will open the connection and do the FilePush, HFT/RF
    #   send_updates_local will just make sure the state is the same on the local machine, EZ

    # the full path apparently doesn't matter
    msg = HostFilePushMessage(host_id, cloud.uname(), cloud.cname(), 'i-dont-give-a-fuck')
    raw_connection.send_obj(msg)

    matching_local_mirror = db.session.query(Cloud).filter_by(my_id_from_remote=host_id).first()
    local_peer = matching_local_mirror is not None

    for update in updates:
        file_path = update[1]
        relative_pathname = os.path.relpath(file_path, cloud.root_directory)
        if update[0] == FILE_CREATE or update[0] == FILE_UPDATE:
            if local_peer:
                send_file_to_local(db, cloud, matching_local_mirror, relative_pathname)
            else:
                send_file_to_other(
                    host_id
                    , cloud
                    , os.path.join(cloud.root_directory, relative_pathname)
                    , raw_connection
                    , recurse=False)

        elif update[0] == FILE_DELETE:
            msg = RemoveFileMessage(host_id, cloud.uname(), cloud.cname(), relative_pathname)
            if local_peer:
                handle_remove_file(host_obj, msg, matching_local_mirror, raw_connection, db)
                mylog('LOCALLY deleted', '32')
                # I echo the above fixme, this is stupid
            else:
                raw_connection.send_obj(msg)
                mylog('Sent a delete', '32')
        else:
            print 'Welp this shouldn\'t happen'
    complete_sending_files(host_id, cloud, None, raw_connection)


def local_file_create(host_obj, directory_path, dir_node, filename, db):
    # type: (HostController, str, FileNode, str, SimpleDB) -> [(int, str)]
    #   where (int, str): (FILE_CREATE, full_path)
    _log = get_mylog()
    _log.debug('Adding {} to filenode for the directory node {}'.format(filename, dir_node.name))
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

    # DO NOT try and set the new node's `cloud` setting. If that's set, then
    #       we'll treat that node as a child of the cloud itself - as a child of
    #       the host.models.Cloud. That's not what we want.
    # Appending the new filenode to the dir_node WILL work, because that will
    #       append it to either the Cloud (if this is a child of the root)
    #       or the FileNode correctly.
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
    # type: (HostController, str, FileNode, str, FileNode, SimpleDB) -> [(int, str)]
    #   where (int, str): (FILE_UPDATE, full_path)
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


def local_file_delete(host_obj, directory_path, dir_node, filename, filenode, db):
    # type: (HostController, str, FileNode, str, FileNode, SimpleDB) -> [(int, str)]
    #   where (int, str): (FILE_DELETE, full_path)
    _log = get_mylog()
    _log.debug('Deleting {} from the directory node {}'.format(filename, dir_node.name))
    # file_pathname = os.path.join(directory_path, filename)
    file_pathname = os.path.join(directory_path, filenode.name)
    # note: filenode is always a filenode. If at all, the dir_node might
    #       be the root (Cloud) node
    # we don't need to recurse for the subdirs of this name
    # we do need to recurse on subnodes
    mirror = filenode.cloud
    # mylog('[{}] Found a deleted file {}'.format(mirror.my_id_from_remote, file_pathname), '33')
    private_data = host_obj.get_private_data(mirror)
    if private_data is None:
        # this is a problem
        err = 'The host doesn\'t have a private data file, that\'s not great'
        mylog(err)

    # if the deleted file was the .nebs, then that's a problem.
    #   regenerate it, and do nothing else.
    if file_pathname == host_obj.is_private_data_file(file_pathname):
        err = 'Hey you there. Don\'t delete the .nebs!'
        mylog(err, '31')
        private_data.commit()
        return
    timestamp = datetime.utcnow()
    deletables = find_deletable_children(filenode, file_pathname, timestamp)
    # deletables should be in reverse BFS order, so as they are deleted they
    #   should have no children
    for full_child_path, node in deletables:
        _log.debug('Deleting child of {} - {}()'.format(dir_node.name, node.name, full_child_path))
        db.session.delete(node)
    # This is safe even on the root filenode (Which is a Cloud object)
    # because the Cloud has children, and because we're not deleting
    # the node it's called on.
    # recursive_child_delete(db, filenode)

    # fortunately, filenode isn't ever the root of the cloud, so delete it too.
    _log.debug('Deleting file node {} ({})'.format(filenode.name, filenode.full_path()))
    db.session.delete(filenode)

    # The .nebs also needs to be updated.
    #   The same subset as in recursive child delete needs to be removed from that file.
    #   **It's the deleter's responsibility to also update the .nebs.**
    relative_deletables = [os.path.relpath(child[0], mirror.root_directory) for child in deletables]

    result = private_data.delete_paths(relative_deletables)
    private_data.commit()
    db.session.commit()
    updates = [(FILE_DELETE, file_pathname)]

    # if result:
    #     updates.append((FILE_UPDATE, private_data.))
    # note: actually, this might update all on it's own on the next update.
    #       Maybe not the best idea, probably should just update it's nodes'
    #       mtime and send it as an update oo, but this is good enough for now.

    # Fortunately, the only change is this one.
    # If it's a palin file, then there's nothing to recurse on.
    # If its a dir, there is no longer anything to recurse on. Deleting this is sufficient.
    # fixme also send the .nebs as a FILE_UPDATE
    return updates


def recursive_child_delete(db, filenode):
    # type: (SimpleDB, FileNode) -> ResultAndData
    # DON'T delete the node it's called on.
    # todo: This needs to be updated to do the right delete action.
    # cont: gather all the nodes in top down, then traverse backwards
    # cont: if any are children of the given node, and they have a newer
    # timestamp then the update, leave that node and direct parents, but not other relatives.
    # (by removing direct parents from the list)
    # This will delete all children of filenode except the ones that have since been updated.
    children_to_delete = filenode.children.all()
    i = 0
    to_delete = len(children_to_delete)
    while i < to_delete:
        child = children_to_delete[i]
        children_to_delete.extend(child.children.all())
        i += 1
        to_delete = len(children_to_delete)
    for child in children_to_delete:
        db.session.delete(child)

FILE_CREATE = 0
FILE_UPDATE = 1
FILE_DELETE = 2


def recursive_local_modifications_check(host_obj, directory_path, dir_node, db):
    # type: (HostController, str, FileNode, SimpleDB) -> [(int, str)]
    """

    :param host_obj:
    :param directory_path: This is the FULL, real path to the file.
    :param dir_node:
    :param db:
    :return:
    """
    _log = get_mylog()
    files = sorted(os.listdir(directory_path), key=lambda filename: filename, reverse=False)
    nodes = dir_node.children.all()
    nodes = sorted(nodes, key=lambda node: node.name, reverse=False)

    i = j = 0
    num_files = len(files)
    num_nodes = len(nodes) if nodes is not None else 0
    original_total_nodes = db.session.query(FileNode).count()
    updates = []

    # mylog('[{}] curr children: <{}>, ({})'.format(mirror_id, files, [node.name for node in nodes]))
    # _log.debug('Iterating over children of {}'.format(directory_path))

    while (i < num_files) and (j < num_nodes):
        # mylog('[{}]Iterating on <{}>, ({})'.format(mirror_id, files[i], nodes[j].name))
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
            delete_updates = local_file_delete(host_obj, directory_path, dir_node, files[i], nodes[j], db)
            updates.extend(delete_updates)
            j += 1
    while i < num_files:  # create the rest of the files
        create_updates = local_file_create(host_obj, directory_path, dir_node, files[i], db)
        updates.extend(create_updates)
        i += 1
    # todo handle j < num_nodes, bulk end deletes
    new_num_nodes = db.session.query(FileNode).count()

    # if not new_num_nodes == original_total_nodes:
    #     mylog('RLM:total file nodes:{}'.format(new_num_nodes))

    return updates


def check_local_modifications(host_obj, cloud, db):
    # type: (HostController, Cloud, SimpleDB) -> None
    root = cloud.root_directory
    updates = recursive_local_modifications_check(host_obj, root, cloud, db)
    if len(updates) > 0:
        send_updates(host_obj, db, cloud, updates)


def new_main_thread(host_obj):
    # type: (HostController) -> None

    db = host_obj.get_instance().make_db_session()

    _log = get_mylog()

    mylog('Beginning to watch for local modifications')
    mirrored_clouds = db.session.query(Cloud).filter_by(completed_mirroring=True)
    num_clouds_mirrored = 0  # mirrored_clouds.count()

    host_obj.handshake_remotes()

    host_obj.acquire_lock()
    host_obj.watchdog_worker.watch_all_clouds(mirrored_clouds.all())
    host_obj.release_lock()

    last_handshake = datetime.utcnow()
    # Why do I do this? Why do I close the session and create a new one?
    db.session.close()

    db = host_obj.get_instance().make_db_session()
    _log.info('entering main loop')

    while not host_obj.is_shutdown_requested():
        # mylog('Top of Loop')
        timed_out = host_obj.network_signal.wait(30)
        host_obj.network_signal.clear()
        host_obj.acquire_lock()
        host_obj.process_connections()
        # mylog('Done processing connections')

        mirrored_clouds = db.session.query(Cloud).filter_by(completed_mirroring=True)
        all_mirrored_clouds = mirrored_clouds.all()

        # update network status will handshake the remotes if we've moved.
        rd = host_obj.update_network_status()
        if rd.success:
            # todo: what if one of the remotes fails to handshake?
            # should store the last handshake per remote
            changed = rd.data
            if changed:
                last_handshake = datetime.utcnow()

        # if the number of mirrors has changed...
        if num_clouds_mirrored < mirrored_clouds.count():
            # todo: if the number of mirrored clouds has changed, observe the new roots
            # TODO: If a cloud is mirrored while we're waiting on the signal, then the
            #       host process won't automatically wake up. We need an inter-process way
            #       to signal that it's time for the thread to wake up again
            _log.info('number of clouds changed.')

            host_obj.watchdog_worker.watch_all_clouds(all_mirrored_clouds)
            _log.info('checking for updates on {}'.format(
                [cloud.my_id_from_remote for cloud in all_mirrored_clouds]
            ))
            num_clouds_mirrored = mirrored_clouds.count()
            # if the number of clouds is different:
            # - handshake all of them
            # - Load the private data for any new ones into memory
            for cloud in all_mirrored_clouds:
                # load_private_data doesn't duplicate existing data
                host_obj.load_private_data(cloud)
            host_obj.handshake_remotes()

            last_handshake = datetime.utcnow()
        # mylog('Done checking for changes to number of clouds')

        # scan the tree for updates
        # mylog('Checking for updates to files')
        for cloud in all_mirrored_clouds:
            # fixme: Make sure that the root of the cloud still exists.
            # cont if not, then the entire mirror was deleted. It should be removed
            #   from the DB, and, we should make sure to tell the remote that the mirror
            #   is inactive/should stop being tracked
            check_local_modifications(host_obj, cloud, db)

        # if more that 30s have passed since the last handshake, handshake
        delta = datetime.utcnow() - last_handshake
        if delta.seconds > 30:
            host_obj.handshake_remotes()
            last_handshake = datetime.utcnow()
        db.session.close()
        host_obj.release_lock()
    _log.info('Leaving main loop')
