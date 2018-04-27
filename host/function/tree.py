import os
from stat import S_ISDIR, S_ISREG

from common_util import validate_cloudname
from host import Cloud
from host.util import get_clouds_by_name
from common.BaseCommand import BaseCommand
from common_util import ResultAndData, Error, Success
from argparse import Namespace
__author__ = 'Mike'


################################################################################
class TreeCommand(BaseCommand):
    def add_parser(self, subparsers):
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
        return tree

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        print_all = args.all
        cloud_name = args.cloud_name
        print_json = args.json
        return _do_db_tree(instance, output_all=print_all, cloudname=cloud_name, use_json=print_json)


def _do_tree(instance, output_all=False, cloudname=None, use_json=False):
    if not output_all and cloudname is None:
        return Error('error: must input a cloudname or use --all to print all clouds')
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
        return Error('No clouds on this host with name {}'.format(cloudname))

    def print_filename(filename, depth):
        print ('--' * depth) + (filename)

    for match in matches:
        print 'tree for {}[{}]<{}>'.format(match.name, match.my_id_from_remote, match.root_directory)
        root_dir = match.root_directory
        walktree(root_dir, 1, print_filename)
    return Success()


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


################################################################################
class DbTreeCommand(BaseCommand):
    def add_parser(self, subparsers):
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
        return db_tree

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        print_all = args.all
        cloud_name = args.cloud_name
        print_json = args.json
        return _do_db_tree(instance, output_all=print_all, cloudname=cloud_name, use_json=print_json)


def _do_db_tree(instance, output_all=False, cloudname=None, use_json=False):
    if not output_all and cloudname is None:
        return Error('error: must input a cloudname or use --all to print all clouds')
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
        return Error('No clouds on this host with name {}'.format(cloudname))

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
    return Success()

################################################################################
