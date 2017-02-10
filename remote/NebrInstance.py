import ConfigParser
import os
from StringIO import StringIO

from common.Instance import Instance, get_from_conf
from remote import models
from common.SimpleDB import SimpleDB


class NebrInstance(Instance):
    def __init__(self, working_dir=None):
        """
        Creates a instance of nebs.
        Attempts to use nebs.conf in the working dir to initialize
        :param working_dir: Working directory for this instance of nebula.
                            Used to store configuration, nebs.db, etc.
                            Can be relative, will be stored as absolute
        """
        if working_dir is None:
            working_dir = './instances/remote/default'
        super(NebrInstance, self).__init__(working_dir)

        # self.host_host = ''
        # self.host_port = 23456
        # self.host_ws_host = '127.0.0.1'
        # self.host_ws_port = 34567

        self._db_name = 'remote.db'
        self._db_models = models.nebr_base
        self._conf_file_name = 'nebr.conf'

        self.init_dir()

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



