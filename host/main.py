import argparse
import sys

from common.BaseCommand import BaseCommand
from common.Instance import Instance
from common_util import *
# from common_util import set_mylog_name, set_mylog_file, mylog, get_log_path
from host.NebsInstance import NebsInstance
from host.HostController import HostController
from host.function.migrate_db import HostMigrateCommand
from host.function.dbg_mirrors import DebugMirrorsCommand
from host.function.dbg_nodes import DebugNodesCommand
from host.function.list_clouds import ListCloudsCommand
from host.function.mirror import MirrorCommand
from host.function.tree import DbTreeCommand, TreeCommand


################################################################################
class StartCommand(BaseCommand):
    def add_parser(self, subparsers):
        start = subparsers.add_parser('start', description='Start the nebula host process')

        start.add_argument('--force'
                            , action='store_true'
                            , help='Force kill any existing nebula host processes')
        start.add_argument('--access', default=None)
        return start

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        force_kill = args.force
        access_log = args.access
        host_controller = HostController(instance)
        return host_controller.start(force_kill=force_kill, access_log=access_log)


################################################################################
class KillCommand(BaseCommand):
    def add_parser(self, subparsers):
        kill = subparsers.add_parser('kill', description='Kill the nebula host process, if it\'s currently running')
        return kill

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        rd = instance.kill()
        return rd

################################################################################

# command_descriptions = {
#     'mirror': '\t\tmirror a remote cloud to this device'
#     , 'start': '\t\tstart the main thread checking for updates'
#     , 'list-clouds': '\tlist all current clouds'
#     , 'tree': '\t\tdisplays the file structure of a cloud on this host.'
#     , 'db-tree': '\tdisplays the db structure of a cloud on this host.'
#     , 'dbg-mirrors': '\tdebug information on the mirrors present on this instance'
#     , 'export-nebs': '\tWrites out the .nebs of matching clouds as json'
#     , 'migrate-db': '\tPerforms a database upgrade. This probably shouldn\'t be callable by the user'
#     , 'kill': '\t\tkills an instance if it\'s running.'
# }


# def usage(instance, argv):
#     print 'usage: nebs <command>'
#     print ''
#     print 'The available commands are:'
#     for command in command_descriptions.keys():
#         print '\t', command, command_descriptions[command]
#     print ''
#     print 'Use [-w, --working-dir <path>] to specify a working dir for the instance,'
#     print ' or [-i, --instance <name>] to provide the instance name'
#     print '                            (same as `-w {nebula path}/instances/host/<name>`)'



def get_nebs_argparser():
    common_parser = setup_common_argparsing()
    nebs_parser = argparse.ArgumentParser(parents=[common_parser])
    # subparsers = parser.add_subparsers(help='sub-command help')
    subparsers = nebs_parser.add_subparsers(dest='command',
                                            title='commands',
                                            description='Nebula Host Commands',
                                            help='Commands for working with the nebula host')
    mirror_cmd = MirrorCommand(subparsers)
    start_cmd = StartCommand(subparsers)
    kill_cmd = KillCommand(subparsers)
    list_clouds_cmd = ListCloudsCommand(subparsers)
    HostMigrateCommand(subparsers)
    TreeCommand(subparsers)
    DbTreeCommand(subparsers)
    DebugNodesCommand(subparsers)
    DebugMirrorsCommand(subparsers)
    return nebs_parser


def nebs_main(argv):

    nebs_argparse = get_nebs_argparser()
    args = nebs_argparse.parse_args()
    log_path = args.log
    log_level = get_level_from_string(args.verbose)

    enable_vt_support()
    config_logger('nebs', log_path, log_level)
    _log = get_mylog()

    if log_path is not None:
        _log.info('Configured logging {}, {}'.format(log_path, log_level))
        print('Writing log to {}'.format(log_path))

    working_dir = Instance.get_working_dir_from_args(args, is_remote=False)
    nebs_instance = NebsInstance(working_dir)

    if args.func:
        result = args.func(nebs_instance, args)
        if result is not None:
            if result.success:
                sys.exit(0)
            else:
                sys.exit(-1)
        else:
            sys.exit(-1)
        # result = 0 if result is None else result
        # sys.exit(result)
    else:
        print('Programming error - The command you entered didnt supply a implementation')
        print('Go add a `set_defaults(func=DO_THE_THING)` to {}'.format(args.command))
    return


if __name__ == '__main__':
    nebs_main(sys.argv)


