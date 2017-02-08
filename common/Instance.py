import ConfigParser
import os
from StringIO import StringIO

from common.SimpleDB import SimpleDB


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
            if arg == '-w' and index < (len(argv) - 1):
                working_dir = argv[index+1]
                remaining_argv.extend(argv[index+2:])
                break
            else:
                remaining_argv.append(arg)

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
        self._db_name = None
        self._db_models = None
        self._conf_file_name = None

    def init_dir(self):
        """
        1. creates the WD if it doesn't exist
        2. Reads data from the working dir
        3. creates the db if it doesn't exist
        """
        # 1.
        exists = os.path.exists(self._working_dir)
        if not exists:
            os.makedirs(self._working_dir)
        else:
            # 2.
            self.load_conf()

        # 3.
        exists = os.path.exists(self._db_path())
        self._db = self.make_db_session()
        self._db.engine.echo = False
        if not exists:
            self._db.create_all_and_repo(self._db_migrate_repo())

    def load_conf(self):
        raise Exception("You shouldn't be using a raw Instance, you should "
                        "extend it or use NebsInstance/NebrInstance")
        # return os.path.join(self._working_dir, 'host.db')

    def _db_uri(self):
        return 'sqlite:///' + self._db_path()

    def _db_migrate_repo(self):
        return os.path.join(self._working_dir, 'db_repository')

    def get_db(self):
        return self._db

    def make_db_session(self):
        return SimpleDB(self._db_uri(), self._db_models)

    def _db_path(self):
        return os.path.join(self._working_dir, self._db_name)

    def get_config_file_path(self):
        return os.path.join(self._working_dir, self._conf_file_name)
