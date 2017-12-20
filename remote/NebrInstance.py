import ConfigParser
import os
from StringIO import StringIO

from common.Instance import Instance, get_from_conf
from common_util import NEBULA_ROOT
from remote import models
from common.SimpleDB import SimpleDB
from common_util import ResultAndData, Error, Success, INSTANCES_ROOT

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
            working_dir = '{}/remote/default'.format(INSTANCES_ROOT)
        super(NebrInstance, self).__init__(working_dir)

        # todo: This is a bit of a hack. Each instance should probably
        #   auto-generate a key/cert, but for now just use the default ones
        self.key_file = os.path.join(NEBULA_ROOT, './remote/remote.key')
        self.cert_file = os.path.join(NEBULA_ROOT, './remote/remote.crt')
        # self.host_ws_host = '127.0.0.1'
        # self.host_ws_port = 34567

        self._db_name = 'remote.db'
        self._db_models = models.nebr_base
        self._conf_file_name = 'nebr.conf'
        self._pid_name = 'nebr'

        self.init_dir()

    def load_conf(self):
        conf_file = self.get_config_file_path()
        if not os.path.exists(conf_file):
            return

        config = ConfigParser.RawConfigParser()
        # TODO: After self reflection, this is dumb. Don't add [root] to the start.
        #       have that in the file itself.
        with open(conf_file) as stream:
            stream = StringIO("[root]\n" + stream.read())
            config.readfp(stream)

            self.key_file = get_from_conf(config, 'KEY', self.key_file)
            self.cert_file = get_from_conf(config, 'CERT', self.cert_file)

    def get_key_file(self):
        return self.key_file

    def get_cert_file(self):
        return self.cert_file




