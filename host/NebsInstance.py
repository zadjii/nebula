import ConfigParser
import os
from StringIO import StringIO

from common.Instance import Instance, get_from_conf
from common_util import NEBULA_ROOT
from host import models
from common.SimpleDB import SimpleDB
from common_util import ResultAndData, Error, Success, INSTANCES_ROOT, mylog


class NebsInstance(Instance):

    def __init__(self, working_dir=None):
        """
        Creates a instance of nebs.
        Attempts to use nebs.conf in the working dir to initialize
        :param working_dir: Working directory for this instance of nebula.
                            Used to store configuration, nebs.db, etc.
                            Can be relative, will be stored as absolute
        """
        if working_dir is None:
            working_dir = '{}/host/default'.format(INSTANCES_ROOT)
        super(NebsInstance, self).__init__(working_dir)

        self.host_host = ''
        self.host_ws_host = '127.0.0.1'
        # Values of 0 will be used by bind() to pick a port automatically.
        self.host_port = 0
        self.host_ws_port = 0
        self.host_internal_port = 0

        # todo: This is a bit of a hack. Each instance should probably
        #   auto-generate a key/cert, but for now just use the default ones
        self.key_file = os.path.join(working_dir, './host.key')
        self.cert_file = os.path.join(working_dir, './host.crt')

        self.local_debug = False

        self._db_name = 'host.db'
        self._db_models = models.nebs_base
        self._conf_file_name = 'nebs.conf'
        self._port_file_name = 'nebs.port'
        self._ip_file_name = 'nebs.ip'
        self._pid_name = 'nebs'

        self.init_dir()

    def _parse_config(self, config=None):
        config = config or self._config

        self.host_port = get_from_conf(config, 'PORT', self.host_port)
        self.host_ws_port = get_from_conf(config, 'WS_PORT', self.host_ws_port)
        self.host_internal_port = get_from_conf(config, 'INTERNAL_PORT', self.host_internal_port)
        self.local_debug = bool(get_from_conf(config, 'LOCAL_DEBUG', self.local_debug))

        self.key_file = get_from_conf(config, 'HOST_KEY', self.key_file)
        self.cert_file = get_from_conf(config, 'HOST_CERT', self.cert_file)

    def get_existing_port(self):
        port = None
        port_file_path = os.path.join(self._working_dir, self._port_file_name)
        if os.path.exists(port_file_path):
            with open(port_file_path, mode='rb') as f:
                port = f.read()
                port = int(port)
        return port

    def persist_port(self, port):
        mylog('persist_port({})'.format(port))
        port_file_path = os.path.join(self._working_dir, self._port_file_name)
        if os.path.exists(port_file_path):
            os.remove(port_file_path)
        with open(port_file_path, mode='wb') as f:
            f.write('{}'.format(port))

    def get_existing_ip(self):
        ip = None
        ip_file_path = os.path.join(self._working_dir, self._ip_file_name)
        if os.path.exists(ip_file_path):
            with open(ip_file_path, mode='rb') as f:
                ip = f.read()
        return ip

    def persist_ip(self, ip):
        mylog('persist_ip({})'.format(ip))
        ip_file_path = os.path.join(self._working_dir, self._ip_file_name)
        if os.path.exists(ip_file_path):
            os.remove(ip_file_path)
        with open(ip_file_path, mode='wb') as f:
            f.write('{}'.format(ip))

    def shutdown(self):
        super(NebsInstance, self).shutdown()
        port_file_path = os.path.join(self._working_dir, self._port_file_name)
        if os.path.exists(port_file_path):
            os.remove(port_file_path)
        ip_file_path = os.path.join(self._working_dir, self._ip_file_name)
        if os.path.exists(ip_file_path):
            os.remove(ip_file_path)




