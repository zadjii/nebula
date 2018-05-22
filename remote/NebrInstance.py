import ConfigParser
import os
from StringIO import StringIO

from common.Instance import Instance, get_from_conf
from common_util import NEBULA_ROOT
from remote import models
from common.SimpleDB import SimpleDB
from common_util import ResultAndData, Error, Success, INSTANCES_ROOT, get_mylog

class NebrInstance(Instance):
    def __init__(self, working_dir=None):
        """
        Creates a instance of nebr.
        Attempts to use nebr.conf in the working dir to initialize
        :param working_dir: Working directory for this instance of nebula.
                            Used to store configuration, nebr.db, etc.
                            Can be relative, will be stored as absolute
        """
        if working_dir is None:
            working_dir = '{}/remote/default'.format(INSTANCES_ROOT)
        super(NebrInstance, self).__init__(working_dir)

        self.key_file = os.path.join(working_dir, './remote.ca.key')
        self.cert_file = os.path.join(working_dir, './remote.ca.chain.crt')
        self.enable_multiple_hosts = False
        self.disable_ssl = False
        self.port = 12345
        # self.host_ws_host = '127.0.0.1'
        # self.host_ws_port = 34567

        self._db_name = 'remote.db'
        self._db_models = models.nebr_base
        self._conf_file_name = 'nebr.conf'
        self._pid_name = 'nebr'

        self.init_dir()

    def load_conf(self):
        _log = get_mylog()
        conf_file = self.get_config_file_path()
        if not os.path.exists(conf_file):
            return

        config = ConfigParser.RawConfigParser()
        with open(conf_file) as stream:
            config.readfp(stream)

            # has_enable = config.has_option('root', 'ENABLE_MULTIPLE_HOSTS')
            # if has_enable:
            #     _log.debug('Has ENABLE_MULTIPLE_HOSTS')
            #     mult_hosts = config.get('root', 'ENABLE_MULTIPLE_HOSTS')
            #     _log.debug(mult_hosts)
            #     _log.debug(False if mult_hosts == '0' else True)
            #     _log.debug(bool(mult_hosts))
            # else:
            #     _log.debug('Doesnt have ENABLE_MULTIPLE_HOSTS')

            self.key_file = get_from_conf(config, 'KEY', self.key_file)
            self.cert_file = get_from_conf(config, 'CERT', self.cert_file)
            _enable_multiple_hosts = get_from_conf(config, 'ENABLE_MULTIPLE_HOSTS', self.enable_multiple_hosts)
            self.enable_multiple_hosts = _enable_multiple_hosts in ['1', 'True', 'true']
            _disable_ssl = get_from_conf(config, 'DISABLE_SSL', self.enable_multiple_hosts)
            self.disable_ssl = _disable_ssl in ['1', 'True', 'true']
            # self.disable_ssl = bool(get_from_conf(config, 'DISABLE_SSL', self.disable_ssl))
            self.port = int(get_from_conf(config, 'PORT', self.port))

    def get_key_file(self):
        return self.key_file

    def get_cert_file(self):
        return self.cert_file

    def is_multiple_hosts_enabled(self):
        return self.enable_multiple_hosts

    def is_ssl_enabled(self):
        return not self.disable_ssl

    def get_port(self):
        return self.port
