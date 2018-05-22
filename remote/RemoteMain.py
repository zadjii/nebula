from common.BaseCommand import BaseCommand
from common.Instance import Instance
from common_util import *
from remote.NebrInstance import NebrInstance
from remote.RemoteController import RemoteController
from remote.function.migrate_db import RemoteMigrateCommand
from remote.function.query_db import ListUsersCommand, ListCloudsCommand, ListHostsCommand
from remote.function.create import CreateCommand


################################################################################
class StartCommand(BaseCommand):
    def add_parser(self, subparsers):
        start = subparsers.add_parser('start', description='Start the nebula remote process')

        start.add_argument('--force'
                            , action='store_true'
                            , help='Force kill any existing nebula remote processes')
        return start

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        remote_controller = RemoteController(instance)
        return remote_controller.start(force_kill=args.force)


################################################################################
class KillCommand(BaseCommand):
    def add_parser(self, subparsers):
        kill = subparsers.add_parser('kill', description='Kill the nebula remote process, if it\'s currently running')
        return kill

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        rd = instance.kill()
        return rd

################################################################################


def get_nebr_argparser():
    common_parser = setup_common_argparsing()
    nebs_parser = argparse.ArgumentParser(parents=[common_parser])
    subparsers = nebs_parser.add_subparsers(dest='command',
                                            title='commands',
                                            description='Nebula Remote Commands',
                                            help='Commands for working with the nebula remote')
    StartCommand(subparsers)
    KillCommand(subparsers)
    CreateCommand(subparsers)
    RemoteMigrateCommand(subparsers)
    ListUsersCommand(subparsers)
    ListCloudsCommand(subparsers)
    ListHostsCommand(subparsers)
    return nebs_parser


def nebr_main(argv):

    nebr_argparse = get_nebr_argparser()
    args = nebr_argparse.parse_args()
    log_path = args.log
    log_level = get_level_from_string(args.verbose)

    enable_vt_support()
    config_logger('nebr', log_path, log_level)
    _log = get_mylog()

    if log_path is not None:
        _log.info('Configured logging {}, {}'.format(log_path, log_level))
        print('Writing log to {}'.format(log_path))

    working_dir = Instance.get_working_dir_from_args(args, is_remote=True)
    nebs_instance = NebrInstance(working_dir)

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
    nebr_main(sys.argv)


