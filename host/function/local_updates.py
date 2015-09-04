from datetime import datetime
import os
from stat import S_ISDIR
import time
from host import FileNode, get_db, Cloud

__author__ = 'Mike'


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
    files = sorted(os.listdir(directory_path), key=lambda filename: filename, reverse=False)

    nodes = dir_node.children.all()
    nodes = sorted(nodes, key=lambda node: node.name, reverse=False)
    i = 0
    j = 0
    num_files = len(files)
    num_nodes = len(nodes) if nodes is not None else 0
    original_total_nodes = db.session.query(FileNode).count()
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
    new_num_nodes = db.session.query(FileNode).count()
    if not new_num_nodes == original_total_nodes:
        print 'total file nodes:', new_num_nodes

    # todo send updates
    # cont Any time a file is updated or a node created, append to a list
    # cont   of updates.
    # cont Get all of the hosts from the remote.
    # cont For each host, we send all of those update/create/deletes out


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