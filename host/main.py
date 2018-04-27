import argparse
import sys

from common.BaseCommand import BaseCommand
from common.Instance import Instance
from common_util import *
# from common_util import set_mylog_name, set_mylog_file, mylog, get_log_path
from host.NebsInstance import NebsInstance
from host.HostController import HostController
from host.function.migrate_db import add_migrate_db_argparser
from host.function.dbg_mirrors import add_dbg_mirrors_argparser
from host.function.dbg_nodes import add_dbg_nodes_argparser
from host.function.list_clouds import add_list_clouds_argparser
from host.function.mirror import mirror, add_mirror_argparser
from host.function.tree import add_db_tree_argparser, add_tree_argparser


################################################################################
def add_start_argparser(subparsers):
    start = subparsers.add_parser('start', description='Start the nebula host process')

    start.add_argument('--force'
                        , action='store_true'
                        , help='Force kill any existing nebula host processes')
    start.set_defaults(func=start_with_args)


def start_with_args(instance, args):
    print('start with args')
    print(args)


def start(instance, argv):
    host_controller = HostController(instance)
    host_controller.start(argv=argv)


################################################################################
class KillCommand(BaseCommand):
    def add_parser(self, subparsers):
        kill = subparsers.add_parser('kill', description='Kill the nebula host process, if it\'s currently running')
        return kill

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        rd = instance.kill()
        print(rd.data)


def add_kill_argparser(subparsers):
    kill = subparsers.add_parser('kill', description='Kill the nebula host process, if it\'s currently running')
    kill.set_defaults(func=kill_with_args)


def kill_with_args(instance, args):
    rd = instance.kill()
    print(rd.data)


# def kill(instance, argv):
#     rd = instance.kill()
#     print(rd.data)


################################################################################
commands = {
    'mirror': mirror  # moved to argparse
    # , 'start': start  # moved to argparse
    # , 'list-clouds': list_clouds  # moved to argparse
    # , 'tree': tree
    # , 'db-tree': db_tree
    # , 'dbg-nodes': dbg_nodes
    # , 'dbg-mirrors': dbg_mirrors
    # , 'migrate-db': migrate_db
    # , 'kill': kill  # moved to argparse
}

command_descriptions = {
    'mirror': '\t\tmirror a remote cloud to this device'
    , 'start': '\t\tstart the main thread checking for updates'
    , 'list-clouds': '\tlist all current clouds'
    , 'tree': '\t\tdisplays the file structure of a cloud on this host.'
    , 'db-tree': '\tdisplays the db structure of a cloud on this host.'
    , 'dbg-mirrors': '\tdebug information on the mirrors present on this instance'
    , 'export-nebs': '\tWrites out the .nebs of matching clouds as json'
    , 'migrate-db': '\tPerforms a database upgrade. This probably shouldn\'t be callable by the user'
    , 'kill': '\t\tkills an instance if it\'s running.'
}


def usage(instance, argv):
    print 'usage: nebs <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]
    print ''
    print 'Use [-w, --working-dir <path>] to specify a working dir for the instance,'
    print ' or [-i, --instance <name>] to provide the instance name'
    print '                            (same as `-w {nebula path}/instances/host/<name>`)'

def setup_common_argparsing():
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('-w', '--working-dir', default=None)
    common_parser.add_argument('-i', '--instance', default=None)
    common_parser.add_argument('-l', '--log', default=None)
    common_parser.add_argument('-v', '--verbose', default=None)
    common_parser.add_argument('--access', default=None)
    return common_parser

def get_nebs_argparser():
    common_parser = setup_common_argparsing()
    nebs_parser = argparse.ArgumentParser(parents=[common_parser])
    # subparsers = parser.add_subparsers(help='sub-command help')
    subparsers = nebs_parser.add_subparsers(dest='command',
                                            title='commands',
                                            description='Nebula Host Commands',
                                            help='Commands for working with the nebula host')
    add_mirror_argparser(subparsers)
    add_start_argparser(subparsers)
    add_kill_argparser(subparsers)
    add_list_clouds_argparser(subparsers)
    add_migrate_db_argparser(subparsers)
    add_tree_argparser(subparsers)
    add_db_tree_argparser(subparsers)
    add_dbg_nodes_argparser(subparsers)
    add_dbg_mirrors_argparser(subparsers)
    return nebs_parser


def nebs_main(argv):

    nebs_argparse = get_nebs_argparser()
    args = nebs_argparse.parse_args()
    # if args.command is None:
    #     args.parse_args(['-h'])
    #     return
    # print(args)
    working_dir = Instance.get_working_dir_from_args(args, is_remote=False)
    nebs_instance = NebsInstance(working_dir)
    log_path = args.log
    log_level = get_level_from_string(args.verbose)

    enable_vt_support()
    config_logger('nebs', log_path, log_level)
    _log = get_mylog()

    if log_path is not None:
        _log.info('Configured logging {}, {}'.format(log_path, log_level))
        print('Writing log to {}'.format(log_path))

    if args.func:
        result = args.func(nebs_instance, args)
        result = 0 if result is None else result
        sys.exit(result)
    else:
        print('Programming error - The command you entered didnt supply a implementation')
        print('Go add a `set_defaults(func=DO_THE_THING)` to {}'.format(args.command))
    return

    # # if there weren't any args, print the usage and return
    # if len(argv) < 2:
    #     usage(None, argv)
    #     sys.exit(0)
    #
    # working_dir, argv = Instance.get_working_dir(argv, is_remote=False)
    # nebs_instance = NebsInstance(working_dir)
    #
    # log_path, argv = get_log_path(argv)
    # log_level, argv = get_log_verbosity(argv)
    #
    # config_logger('nebs', log_path, log_level)
    # _log = get_mylog()
    #
    # _log.info('Configured logging {}, {}'.format(log_path, log_level))
    # if log_path is not None:
    #     print('Writing log to {}'.format(log_path))
    #
    # _log.debug('DB URI: {}'.format(nebs_instance._db_uri()))
    #
    # # if there weren't any args, print the usage and return
    # # Do this again, because get_working_dir may have removed all the args
    # if len(argv) < 2:
    #     usage(None, argv)
    #     sys.exit(0)
    #
    # command = argv[1]
    #
    # selected = commands.get(command, usage)
    # enable_vt_support()
    # result = selected(nebs_instance, argv[2:])
    # result = 0 if result is None else result
    # sys.exit(result)


if __name__ == '__main__':
    nebs_main(sys.argv)


