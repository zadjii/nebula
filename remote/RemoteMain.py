import sys

from common.BaseCommand import BaseCommand
from common.Instance import Instance
from common_util import *
from remote.NebrInstance import NebrInstance
from remote.RemoteController import RemoteController
from remote.function.migrate_db import RemoteMigrateCommand

from remote.function.query_db import ListUsersCommand, ListCloudsCommand, ListHostsCommand
from remote.function.create import CreateCommand
from remote.function.new_user import new_user


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



# def kill(instance, argv):
#     rd = instance.kill()
#     print(rd.data)


# commands = {
#     'new-user': new_user # we're deprecating this entirely, it's useless
#     , 'start': start
#     , 'create': create
#     , 'list-users': list_users
#     , 'list-clouds': list_clouds
#     , 'migrate-db': migrate_db
#     , 'kill': kill
#     , 'list-hosts': list_hosts
# }
# command_descriptions = {
    # 'new-user': '\tadd a new user to the database'
    # , 'start': '\t\tstart the remote server'
    # , 'create': '\t\tcreate a new cloud to track'
    # , 'list-users': '\tlist all current users'
    # , 'list-clouds': '\tlist all current clouds'
    # , 'migrate-db': '\tPerforms a database upgrade. This probably shouldn\'t be callable by the user'
    # , 'kill': '\t\tkills an instance if it\'s running.'
    # , 'list-hosts': '\t\tLists details about hosts'
# }


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



# def usage(instamce, argv):
#     print 'usage: nebr <command>'
#     print ''
#     print 'The available commands are:'
#     for command in command_descriptions.keys():
#         print '\t', command, command_descriptions[command]


def nebr_main(argv):

    nebr_argparse = get_nebr_argparser()
    args = nebr_argparse.parse_args()
    working_dir = Instance.get_working_dir_from_args(args, is_remote=True)
    nebs_instance = NebrInstance(working_dir)
    log_path = args.log
    log_level = get_level_from_string(args.verbose)

    enable_vt_support()
    config_logger('nebr', log_path, log_level)
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
    # if len(argv) < 2:
    #     usage(None, argv)
    #     sys.exit(0)
    #
    # working_dir, argv = Instance.get_working_dir(argv, True)
    # log_path, argv = get_log_path(argv)
    # log_level, argv = get_log_verbosity(argv)
    #
    # config_logger('nebr', log_path, log_level)
    # _log = get_mylog()
    #
    # _log.info('Configured logging {}, {}'.format(log_path, log_level))
    # if log_path is not None:
    #     print 'Writing log to {}'.format(log_path)
    #
    # nebr_instance = NebrInstance(working_dir)
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
    # selected(nebr_instance, argv[2:])
    # sys.exit(0)

if __name__ == '__main__':
    nebr_main(sys.argv)


