import ConfigParser
import logging
import os
import imp

import threading
from StringIO import StringIO

import thread

import subprocess

import signal

from migrate.versioning import api

from common.SimpleDB import SimpleDB
from common_util import *
import time


def get_from_conf(config, key, default):
    return config.get('root', key) \
        if config.has_option('root', key) else default


class Instance(object):

    @staticmethod
    def get_working_dir(argv, is_remote=False):
        # type: ([str]) -> (str, [str])
        """
        If there's a [-w <path>] or [--working-dir <path>] in argv,
        it removes the pair and returns it.
        Else it returns None

        :param argv:
        :param is_remote: If the instance is a remote instance or a host instance
        :return: (path, [argv] - [-w, path]) or (None, argv)
        """
        # print('initial argv={}'.format(argv))
        remaining_argv = []
        working_dir = None
        instance_type = 'remote' if is_remote else 'host'
        for index, arg in enumerate(argv):
            if index >= (len(argv) - 1):
                remaining_argv.append(arg)
            if (arg == '-w') or (arg == '--working-dir'):
                working_dir = argv[index+1]
                remaining_argv.extend(argv[index+2:])
                break
            if (arg == '-i') or (arg == '--instance'):
                working_dir = os.path.join('{}/{}/'.format(INSTANCES_ROOT, instance_type), argv[index+1])
                remaining_argv.extend(argv[index+2:])
                break
            else:
                remaining_argv.append(arg)

        # print('remaining_argv={}'.format(remaining_argv))
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
            raise Exception('You should not be calling Instance::__init__ without a working_dir param! THe sub-classes need to set that!')
            # working_dir = '{}/default'.format(INSTANCES_ROOT)

        self._working_dir = os.path.abspath(working_dir)
        self._db = None
        self._db_name = None
        self._db_models = None
        self._conf_file_name = None
        self._db_map = {}
        self._pid_name = None

    def get_instance_name(self):
        return os.path.split(self._working_dir)[1]

    def get_full_name(self):
        return self._pid_name + self.get_instance_name()

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
        thread_id = thread.get_ident()

        if not (thread_id in self._db_map.keys()):
            db = self.make_db_session()
            self._db_map[thread_id] = db

        return self._db_map[thread_id]

    def make_db_session(self):
        db = SimpleDB(self._db_uri(), self._db_models)
        db.engine.echo = False
        return db

    def _db_path(self):
        return os.path.join(self._working_dir, self._db_name)

    def get_config_file_path(self):
        return os.path.join(self._working_dir, self._conf_file_name)

    def _get_pid_file_path(self):
        pid_file = os.path.join(self._working_dir, '{}.pid'.format(self._pid_name))
        return pid_file

    def start(self, force=False):
        # type: (bool) -> ResultAndData
        pid_file = self._get_pid_file_path()
        rd = Error()
        if os.path.exists(pid_file):
            if force:
                rd = self.kill()
                # if rd.success:
                #     print(rd.data)
            else:
                return Error('Process already exists')
        handle = open(pid_file, mode='wb')
        pid = os.getpid()
        handle.write(str(pid))
        handle.close()
        return Success(pid)

    def kill(self):
        rd = Error()
        pid_file = self._get_pid_file_path()
        if os.path.exists(pid_file):
            with open(pid_file) as handle:
                pid = handle.read()
                _log = get_mylog()
                _log.debug(pid)
                os.kill(int(pid), signal.SIGTERM)
                rd = Success('Successfully killed process {}'.format(pid))

            time.sleep(.5)
            self.shutdown()
        else:
            rd = Success('No process is already running for working directory {}'.format(self._working_dir))

        return rd


    def shutdown(self):
        pid_file = self._get_pid_file_path()
        if os.path.exists(pid_file):
            os.remove(pid_file)
        pass

    def migrate(self):
        repo = self._db_migrate_repo()
        uri = self._db_uri()
        db = self.get_db()
        migration_name = '%04d_migration.py' % (api.db_version(uri, repo) + 1)
        migration = repo + '/versions/' + migration_name
        tmp_module = imp.new_module('old_model')
        old_model = api.create_model(uri, repo)
        exec old_model in tmp_module.__dict__
        script = api.make_update_script_for_model(uri, repo, tmp_module.meta, db.Base.metadata)
        open(migration, "wt").write(script)
        api.upgrade(uri, repo)
        print 'New migration saved as ' + migration
        print 'Current database version: ' + str(api.db_version(uri, repo))
        api.upgrade(uri, repo)
        print 'New database version: ' + str(api.db_version(uri, repo))





