import sys

from common.Instance import Instance
from common_util import enable_vt_support
from host.NebsInstance import NebsInstance
from host.HostController import HostController
from host.function.migrate_db import migrate_db
from host.function.dbg_mirrors import dbg_mirrors
from host.function.dbg_nodes import dbg_nodes
from host.function.list_clouds import list_clouds
from host.function.mirror import mirror
from host.function.tree import tree, db_tree


def start(instance, argv):
    host_controller = HostController(instance)
    host_controller.start(argv=argv)

def kill(instance, argv):
    rd = instance.kill()
    print(rd.data)


commands = {
    'mirror': mirror
    , 'start': start
    , 'list-clouds': list_clouds
    , 'tree': tree
    , 'db-tree': db_tree
    , 'dbg-nodes': dbg_nodes
    , 'dbg-mirrors': dbg_mirrors
    , 'migrate-db': migrate_db
    , 'kill': kill
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
    print '                            (same as `-w ./instances/host/<name>`)'


def nebs_main(argv):

    # if there weren't any args, print the usage and return
    if len(argv) < 2:
        usage(None, argv)
        sys.exit(0)

    working_dir, argv = Instance.get_working_dir(argv, is_remote=False)
    nebs_instance = NebsInstance(working_dir)

    # if there weren't any args, print the usage and return
    # Do this again, because get_working_dir may have removed all the args
    if len(argv) < 2:
        usage(None, argv)
        sys.exit(0)

    command = argv[1]

    selected = commands.get(command, usage)
    enable_vt_support()
    result = selected(nebs_instance, argv[2:])
    result = 0 if result is None else result
    sys.exit(result)


if __name__ == '__main__':
    nebs_main(sys.argv)
