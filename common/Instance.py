import ConfigParser
import os
import imp
import thread
import signal
from argparse import Namespace

from inspect import getframeinfo, currentframe

import psutil
import sys
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
            elif (arg == '-w') or (arg == '--working-dir'):
                working_dir = argv[index+1]
                remaining_argv.extend(argv[index+2:])
                break
            elif (arg == '-i') or (arg == '--instance'):
                working_dir = os.path.join('{}/{}/'.format(INSTANCES_ROOT, instance_type), argv[index+1])
                remaining_argv.extend(argv[index+2:])
                break
            else:
                remaining_argv.append(arg)

        # print('remaining_argv={}'.format(remaining_argv))
        return working_dir, remaining_argv

    @staticmethod
    def get_working_dir_from_args(args, is_remote=False):
        # type: (Namespace) -> (str)
        """
        """
        working_dir = args.working_dir
        instance_type = 'remote' if is_remote else 'host'
        if args.instance:
            working_dir = os.path.join('{}/{}/'.format(INSTANCES_ROOT, instance_type), args.instance)
        return working_dir

    def __init__(self, working_dir=None, unittesting=False):
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
        self._config = None
        self._unittesting = unittesting

    def get_instance_name(self):
        return os.path.split(self._working_dir)[1]

    def get_full_name(self):
        return self._pid_name + self.get_instance_name()

    def init_dir(self):
        _log = get_mylog()
        """
        1. creates the WD if it doesn't exist
        2. Reads data from the working dir
        3. creates the db if it doesn't exist
        """
        # 1.
        if not self._unittesting:
            exists = os.path.exists(self._working_dir)
            if not exists:
                os.makedirs(self._working_dir)
            else:
                # 2.
                self.load_conf()

        # 3.
        doesnt_exist = self._unittesting or not os.path.exists(self._db_path())
        self._db = self.make_db_session()
        self._db.engine.echo = False
        if doesnt_exist:
            if self._unittesting:
                # Don't create the database here:
                # For whatever reason, if you create the database here, (during TestCase.setUp),
                # then try to access it later, (using HostController.get_instance().get_db()), its
                # as if the DB doesn't exist at all. I don't know why, I feel like it should work.
                # In unittests, you should make sure to create the DB manually.
                # see HostControllerTests.
                # self._db.create_all()
                _log.debug('The database should have already been created manually for unittesting.')
            else:
                self._db.create_all_and_repo(self._db_migrate_repo())
                _log.debug('The database ({}) should have been created here'.format(self._db_path()))
                _log.debug('The migration repo should have been created here')

    def _parse_config(self, config=None):
        """
        config param exists so we can test this. Use the config param if it
        exists, otherwise default to the self._config.
        """
        raise Exception("You shouldn't be using a raw Instance, you should "
                        "extend it or use NebsInstance/NebrInstance")

    def load_conf(self):
        conf_file = self.get_config_file_path()
        if not os.path.exists(conf_file):
            return

        config = ConfigParser.RawConfigParser()
        with open(conf_file) as stream:
            config.readfp(stream)
            self._config = config
        self._parse_config()

    def _db_uri(self):
        # type: () -> str
        return 'sqlite:///' + ('' if self._unittesting else self._db_path())

    def _db_migrate_repo(self):
        return os.path.join(self._working_dir, 'db_repository')

    def get_db(self):
        thread_id = thread.get_ident()

        frameinfo = getframeinfo(currentframe().f_back)
        caller = getframeinfo(currentframe().f_back.f_back)
        get_mylog().debug('Calling get_db - {}/{}:{}'.format(os.path.basename(caller.filename),
                                                           os.path.basename(frameinfo.filename),
                                                           frameinfo.lineno))

        if not (thread_id in self._db_map.keys()):
            db = self.make_db_session()
            get_mylog().debug('Created new session')
            self._db_map[thread_id] = db
        else:
            get_mylog().debug('found existing session')

        return self._db_map[thread_id]

    def make_db_session(self):
        # type: () -> SimpleDB
        db = SimpleDB(self._db_uri(), self._db_models)
        db.engine.echo = False
        return db


    def close_db(self):
        thread_id = thread.get_ident()

        frameinfo = getframeinfo(currentframe().f_back)
        caller = getframeinfo(currentframe().f_back.f_back)
        get_mylog().debug('Calling close_db - {}/{}:{}'.format(os.path.basename(caller.filename),
                                                           os.path.basename(frameinfo.filename),
                                                           frameinfo.lineno))

        if (thread_id in self._db_map.keys()):
            get_mylog().debug('Closing existing session')
            self._db_map[thread_id].session.close()
            self._db_map[thread_id] = None
            self._db_map.pop(thread_id)
        else:
            get_mylog().debug('no existing session to close')

    def _db_path(self):
        return os.path.join(self._working_dir, self._db_name)

    def get_config_file_path(self):
        return os.path.join(self._working_dir, self._conf_file_name)

    def _get_pid_file_path(self):
        pid_file = os.path.join(self._working_dir, '{}.pid'.format(self._pid_name))
        return pid_file

    def start(self, force=False):
        # type: (bool) -> ResultAndData
        _log = get_mylog()
        my_pid = os.getpid()
        rd = Error()
        other_pids = Instance.get_other_processes()
        _log.debug('found other processes: {}'.format(other_pids))
        if force:
            rd = Instance.kill_pids(other_pids)
        else:
            if len(other_pids) > 0:
                msg = 'Process already exists'
                _log.error(msg)
                rd = Error(msg)
            else:
                rd = Success()
        if rd.success:
            rd = Success(my_pid)
        return rd

    @staticmethod
    def kill_pids(pids):
        rd = Success()
        _log = get_mylog()
        try:
            for pid in pids:
                process = psutil.Process(pid)
                _log.info('Killing existing process {}'.format(pid))
                process.kill()
        except Exception:
            rd = Error('Failed to kill other instances')
        return rd

    @staticmethod
    def get_other_processes(argv=None):
        _log = get_mylog()
        my_pid = os.getpid()
        argv = sys.argv if argv is None else argv
        pids = Instance._get_existing_process(argv)
        _log.debug('Found these processes={}'.format(pids))
        other_pids = [p for p in pids if p != my_pid]
        _log.debug('These are the other ones={}'.format(other_pids))
        return other_pids

    @staticmethod
    def _get_existing_process(argv=None):
        # type: () -> List[int]
        _log = get_mylog()
        argv = sys.argv if argv is None else argv
        # process_name = argv[0]
        _log.debug('These are my args={}'.format(argv))
        matching_pids = []
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                pname = p.name()
                is_python = pname in ['python', 'python.exe', 'py', 'py.exe']
                if is_python and Instance._is_process_running_instance(p):
                    matching_pids.append(pid)
            except psutil.NoSuchProcess:
                pass
        return matching_pids

    @staticmethod
    def _is_process_running_instance(process):
        _log = get_mylog()
        argv = sys.argv
        process_name = argv[0]
        # _log.debug('These are my args={}'.format(argv))
        try:
            cmdline = process.cmdline()
            # _log.debug('is {} an nebula({}) instance?'.format(cmdline, process_name))
            if process.cmdline() > 2:
                is_us = process_name in cmdline[1]
                is_start = 'start' in cmdline
                if is_us and is_start:
                    # _log.debug('\t Yes it is!')
                    return True

        except Exception, e:
            # _log.error('Error checking if pid({}, \'{}\') is a running instance of nebula'.format(process.pid, process.name()))
            pass
        return False

    def kill(self):
        rd = Error()

        _log = get_mylog()
        my_pid = os.getpid()
        # other_pids = Instance.get_other_processes(['-i', self.get_instance_name()])
        other_pids = Instance.get_other_processes()
        rd = Instance.kill_pids(other_pids)
        # pid_file = self._get_pid_file_path()
        # if os.path.exists(pid_file):
        #     with open(pid_file) as handle:
        #         pid = handle.read()
        #         _log = get_mylog()
        #         _log.debug(pid)
        #         os.kill(int(pid), signal.SIGTERM)
        #         rd = Success('Successfully killed process {}'.format(pid))
        #
        #     time.sleep(.5)
        #     self.shutdown()
        # else:
        #     rd = Success('No process is already running for working directory {}'.format(self._working_dir))

        return rd

    def shutdown(self):
        _log = get_mylog()
        _log.debug('Instance.shutdown')
        pid_file = self._get_pid_file_path()
        if os.path.exists(pid_file):
            _log.debug('Instance.shutdown - removing pid file')
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





