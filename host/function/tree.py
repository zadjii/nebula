import os
from stat import S_ISDIR, S_ISREG

from common_util import validate_cloudname
from host import Cloud
from host.util import get_clouds_by_name

__author__ = 'Mike'


################################################################################
def add_tree_argparser(subparsers):
    tree = subparsers.add_parser('tree', description='displays the file structure of a cloud on this host, as it appears on disk')
    tree.add_argument('-a', '--all'
                      , action='store_true'
                      , help='Print for all clouds on this host')

    tree.add_argument('-j', '--json'
                      , action='store_true'
                      , help='Output the tree as a json blob')
    tree.add_argument('cloud_name', metavar='cloud-name'
                      , nargs='?'
                      , help='Name of the cloud to print the tree for, in <username>/<cloudname> format')
    tree.set_defaults(func=tree_with_args)


def tree_with_args(instance, args):
    print_all = args.all
    cloud_name = args.cloud_name
    print_json = args.json
    return _do_db_tree(instance, output_all=print_all, cloudname=cloud_name, use_json=print_json)


################################################################################
def add_db_tree_argparser(subparsers):
    db_tree = subparsers.add_parser('db-tree', description='displays the file structure of a cloud on this host, as it appears in the nebula DB')

    db_tree.add_argument('-a', '--all'
                         , action='store_true'
                         , help='Print for all clouds on this host')

    db_tree.add_argument('-j', '--json'
                         , action='store_true'
                         , help='Output the tree as a json blob')
    db_tree.add_argument('cloud_name', metavar='cloud-name'
                        , nargs='?'
                        , help='Name of the cloud to print the tree for, in <username>/<cloudname> format')
    db_tree.set_defaults(func=db_tree_with_args)


def db_tree_with_args(instance, args):
    print_all = args.all
    cloud_name = args.cloud_name
    print_json = args.json
    return _do_db_tree(instance, output_all=print_all, cloudname=cloud_name, use_json=print_json)

################################################################################

#
# def db_tree_usage():
#     print 'usage: neb tree (-j)(-a)[cloudname]'
#     print ''
#
#
# def tree_usage():
#     print 'usage: neb tree (-j)(-a)[cloudname]'
#     print ''


# def db_tree(instance, argv):
#     if len(argv) < 1:
#         db_tree_usage()
#         return
#     print 'tree', argv
#     output_json = False
#     output_all = False
#     cloudname = None
#     while len(argv) > 0:
#         arg = argv[0]
#         args_left = len(argv)
#         args_eaten = 0
#         if arg == '-j':
#             output_json = True
#             args_eaten = 1
#         if arg == '-a':
#             output_all = True
#             args_eaten = 1
#         else:
#             cloudname = arg
#             args_eaten = 1
#         argv = argv[args_eaten:]
#     if cloudname is None:
#         raise Exception('Must specify a cloud name to mirror')
#     return _do_tree(instance, output_all=output_all, cloudname=cloudname, use_json=output_json)

def _do_db_tree(instance, output_all=False, cloudname=None, use_json=False):
    if not output_all and cloudname is None:
        print('error: must input a cloudname or use --all to print all clouds')
        return
    db = instance.get_db()
    matches = []
    if output_all:
        matches = db.session.query(Cloud).all()
    else:
        rd = validate_cloudname(cloudname)
        if rd.success:
            uname, cname = rd.data
            matches = get_clouds_by_name(db, uname, cname)
    if len(matches) == 0:
        print('No clouds on this host with name {}'.format(cloudname))
        return

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


# def tree(instance, argv):
#     if len(argv) < 1:
#         tree_usage()
#         return
#     print 'tree', argv
#     output_json = False
#     output_all = False
#     cloudname = None
#     while len(argv) > 0:
#         arg = argv[0]
#         args_left = len(argv)
#         args_eaten = 0
#         if arg == '-j':
#             output_json = True
#             args_eaten = 1
#         if arg == '-a':
#             output_all = True
#             args_eaten = 1
#         else:
#             cloudname = arg
#             args_eaten = 1
#         argv = argv[args_eaten:]
#     _do_tree(instance, output_all=output_all, cloudname=cloudname, use_json=output_json)


def _do_tree(instance, output_all=False, cloudname=None, use_json=False):
    if not output_all and cloudname is None:
        print('error: must input a cloudname or use --all to print all clouds')
        return
    db = instance.get_db()
    matches = []
    if output_all:
        matches = db.session.query(Cloud).all()
    else:
        rd = validate_cloudname(cloudname)
        if rd.success:
            uname, cname = rd.data
            matches = get_clouds_by_name(db, uname, cname)
    if len(matches) == 0:
        print('No clouds on this host with name {}'.format(cloudname))
        return

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
