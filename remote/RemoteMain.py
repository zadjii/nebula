import sys

from common.Instance import Instance
from remote.NebrInstance import NebrInstance
from remote.RemoteController import RemoteController
from remote.function.query_db import list_users, list_clouds
from remote.function.create import create
from remote.function.new_user import new_user


def start(instance, argv):
    remote_controller = RemoteController(instance)
    remote_controller.start(argv=argv)

commands = {
    'new-user': new_user
    , 'start': start
    , 'create': create
    , 'list-users': list_users
    , 'list-clouds': list_clouds
}
command_descriptions = {
    'new-user': '\tadd a new user to the database'
    , 'start': '\t\tstart the remote server'
    , 'create': '\t\tcreate a new cloud to track'
    , 'list-users': '\tlist all current users'
    , 'list-clouds': '\tlist all current clouds'
}


def usage(instamce, argv):
    print 'usage: nebr <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]


def nebr_main(argv):
    if len(argv) < 2:
        usage(None, argv)
        sys.exit(0)

    working_dir, argv = Instance.get_working_dir(argv, True)
    nebr_instance = NebrInstance(working_dir)

    command = argv[1]

    selected = commands.get(command, usage)
    selected(nebr_instance, argv[2:])
    sys.exit(0)

if __name__ == '__main__':
    nebr_main(sys.argv)


