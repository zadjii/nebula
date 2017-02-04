import ConfigParser
import os
from StringIO import StringIO


def get_from_conf(config, key, default):
    return config.get('root', key) \
        if config.has_option('root', key) else default


class Instance(object):

    @staticmethod
    def get_working_dir(argv):
        # type: ([str]) -> (str, [str])
        """
        If there's a [-w <path>] or [--working-dir <path>] in argv,
        it removes the pair and returns it.
        Else it returns None

        :param argv:
        :return: (path, [argv] - [-w, path]) or (None, argv)
        """
        remaining_argv = []
        working_dir = None
        for index, arg in enumerate(argv):
            print arg
            if arg == '-w' and index < (len(argv) - 1):
                working_dir = argv[index+1]
                remaining_argv.extend(argv[index+2:])
                break
            else:
                remaining_argv.append(arg)
            print remaining_argv

        return working_dir, remaining_argv

    def __init__(self, working_dir=None):
        """
        Creates a instance of nebs.
        Attempts to use nebs.conf in the working dir to initialize
        :param working_dir: Working directory for this instance of nebula.
                            Used to store configuration, nebs.db, etc.
                            Can be relative, will be stored as absolute
        """
        if working_dir is None:
            working_dir = './instances/default'

        self._working_dir = os.path.abspath(working_dir)
        self._db = None

    def _db_path(self):
        raise Exception("You shouldn't be using a raw Instance, you should "
                        "extend it or use NebsInstance/NebrInstance")
        # return os.path.join(self._working_dir, 'host.db')

    def _db_uri(self):
        return 'sqlite:///' + self._db_path()

    def _db_migrate_repo(self):
        return os.path.join(self._working_dir, 'db_repository')

    def get_db(self):
        return self._db
