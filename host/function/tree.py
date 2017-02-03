import os
from stat import S_ISDIR, S_ISREG
from host import Cloud

__author__ = 'Mike'


def db_tree_usage():
    print 'usage: neb tree (-j)(-a)[cloudname]'
    print ''


def tree_usage():
    print 'usage: neb tree (-j)(-a)[cloudname]'
    print ''


def db_tree(instance, argv):
    db = instance.get_db()
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
    # match = db.session.query(Cloud).filter_by(name=cloudname).first()
    matches = db.session.query(Cloud).filter_by(name=cloudname).all()
    if len(matches) == 0:
        raise Exception('No clouds on this host with name', cloudname)

    def print_filename(file_node, depth):
        print ('--' * depth) + (file_node.name)

    def walk_db_recursive(file_node, depth, callback):
        callback(file_node, depth)
        for child in file_node.children.all():
            walk_db_recursive(child, depth+1, print_filename)

    for match in matches:
        print 'db-tree for {}[{}]<{}>'.format(match.name, match.my_id_from_remote, match.root_directory)
        for top_level_node in match.children.all():
            walk_db_recursive(top_level_node, 1, print_filename)


def tree(instance, argv):
    db = instance.get_db()
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
    # match = db.session.query(Cloud).filter_by(name=cloudname).first()
    matches = db.session.query(Cloud).filter_by(name=cloudname).all()
    if len(matches) == 0:
        raise Exception('No clouds on this host with name', cloudname)

    def print_filename(filename, depth):
        print ('--' * depth) + (filename)

    for match in matches:
        print 'tree for {}[{}]<{}>'.format(match.name, match.my_id_from_remote, match.root_directory)
        root_dir = match.root_directory
        walktree(root_dir, 1, print_filename)


def walktree(top, depth, callback):
    """recursively descend the directory tree rooted at top,
       calling the callback function for each regular file"""

    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        mode = os.stat(pathname).st_mode
        if S_ISDIR(mode):  # It's a directory, recurse into it
            callback(f, depth)
            walktree(pathname, depth+1, callback)
        elif S_ISREG(mode):  # It's a file, call the callback function
            callback(f, depth)
        else:  # Unknown file type, print a message
            print 'Skipping %s' % pathname
