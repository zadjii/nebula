import ConfigParser
import os
from StringIO import StringIO

from common.Instance import Instance
from host import SimpleDB, models


def get_from_conf(config, key, default):
    return config.get('root', key) \
        if config.has_option('root', key) else default


class NebsInstance(Instance):

    def __init__(self, working_dir=None):
        """
        Creates a instance of nebs.
        Attempts to use nebs.conf in the working dir to initialize
        :param working_dir: Working directory for this instance of nebula.
                            Used to store configuration, nebs.db, etc.
                            Can be relative, will be stored as absolute
        """
        super(NebsInstance, self).__init__(working_dir)

        self.host_host = ''
        self.host_port = 23456
        self.host_ws_host = '127.0.0.1'
        self.host_ws_port = 34567

        self.init_dir()

    def init_dir(self):
        """
        creates the WD if it doesn't exist
        Reads data from the working dir
        creates the db if it doesn't exist
        """
        exists = os.path.exists(self._working_dir)
        if not exists:
            os.makedirs(self._working_dir)
        else:
            self.load_conf()

        exists = os.path.exists(self._db_path())

        self._db = SimpleDB(self._db_uri(), models.nebs_base)
        self._db.engine.echo = False
        if not exists:
            self._db.create_all_and_repo(self._db_migrate_repo())

        #fixme SHIT
        # The Models are all initialized with the global _host_db import

    def load_conf(self):
        conf_file = self.get_config_file_path()
        if not os.path.exists(conf_file):
            return

        config = ConfigParser.RawConfigParser()
        with open(conf_file) as stream:
            stream = StringIO("[root]\n" + stream.read())
            config.readfp(stream)

            self.host_port = get_from_conf(config, 'PORT', self.host_port)
            self.host_ws_port = get_from_conf(config, 'WS_PORT', self.host_ws_port)

    def _db_path(self):
        return os.path.join(self._working_dir, 'host.db')

    # def _db_uri(self):
    #     return 'sqlite:///' + self._db_path()
    #
    # def _db_migrate_repo(self):
    #     return os.path.join(self._working_dir, 'db_repository')

    def get_config_file_path(self):
        return os.path.join(self._working_dir, 'nebs.conf')


