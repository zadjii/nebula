import ctypes
import os
import platform
import posixpath
from logging import *
import logging.handlers
from os import path
from datetime import datetime
###############################################################################
import sys

NEBULA_ROOT = path.abspath(path.dirname(__file__))
INSTANCES_ROOT = path.abspath(path.join(NEBULA_ROOT, './instances'))
###############################################################################
INVALID_HOST_ID = -1
###############################################################################
PUBLIC_USER_ID = -1
###############################################################################
# ClientUpgradeConnection message types:
# This has to be updated manually, which is kinda shitty.
# If add anything here, update socket_common.js as well.
ENABLE_ALPHA_ENCRYPTION = 1
###############################################################################
from collections import namedtuple
ResultAndData = namedtuple('ResultAndData', 'success, data')
def Error(data=None):
    return ResultAndData(False, data)
def Success(data=None):
    return ResultAndData(True, data)
###############################################################################
__author__ = 'Mike'

_log = None


def get_mylog():
    global _log
    return _log


def config_logger(name='nebula', filename=None, level=logging.INFO):
    global _log
    if _log is not None:
        return
    _log = getLogger(name)
    for h in _log.handlers:
        _log.removeHandler(h)
    if filename is None:
        hdlr = logging.StreamHandler()
    else:
        # todo: make this a configurable number of bytes
        hdlr = logging.handlers.RotatingFileHandler(
                filename, maxBytes=100*1024*1024, backupCount=5)
    _log.setLevel(level)
    formatter = logging.Formatter('%(asctime)s|[%(name)s](%(levelname)s) %(message)s')
    hdlr.setFormatter(formatter)
    _log.addHandler(hdlr)
    _log.propagate = False


mylog_name = None
mylog_file = None


def set_mylog_name(name):
    pass


def set_mylog_file(filename):
    pass


def mylog(message, sgr_seq='0'):
    __log = get_mylog()
    if not __log:
        print('Fool! You have\'nt configured the log yet!')
        print(message)
        return

    __log.info(message)


def enable_vt_support():
    if os.name == 'nt':
        import ctypes
        hOut = ctypes.windll.kernel32.GetStdHandle(-11)
        out_modes = ctypes.c_uint32()
        ENABLE_VT_PROCESSING = ctypes.c_uint32(0x0004)
        # ctypes.addressof()
        ctypes.windll.kernel32.GetConsoleMode(hOut, ctypes.byref(out_modes))
        out_modes = ctypes.c_uint32(out_modes.value | 0x0004)
        ctypes.windll.kernel32.SetConsoleMode(hOut, out_modes)


def get_log_path(argv):
    # type: ([str]) -> (str, [str])
    """
    If there's a [-l <path>] or [--log <path>] in argv,
    it removes the pair and returns it.
    Else it returns None

    :param argv:
    :return: (path, [argv] - [-l, path]) or (None, argv)
    """
    # print('initial argv={}'.format(argv))
    remaining_argv = []
    log_path = None
    for index, arg in enumerate(argv):
        if index >= (len(argv) - 1):
            remaining_argv.append(arg)
        if (arg == '-l') or (arg == '--log'):
            log_path = argv[index+1]
            remaining_argv.extend(argv[index+2:])
            break
        else:
            remaining_argv.append(arg)

    # print('remaining_argv={}'.format(remaining_argv))
    return log_path, remaining_argv


def get_log_verbosity(argv):
    # type: ([str]) -> (int, [str])
    """
    If there's a [-v <level>] or [--verbose <level>] in argv,
    it removes the pair and returns a matching logging level
    Else it returns logging.INFO

    :param argv:
    :return: (int, [argv] - [-l, path]) or (logging.INFO, argv)
    """
    # print('initial argv={}'.format(argv))
    remaining_argv = []
    verbosity = None
    log_level = logging.INFO
    for index, arg in enumerate(argv):
        if index >= (len(argv) - 1):
            remaining_argv.append(arg)
        if (arg == '-v') or (arg == '--verbose'):
            verbosity = argv[index+1]
            remaining_argv.extend(argv[index+2:])
            break
        else:
            remaining_argv.append(arg)

    if verbosity == 'debug'\
            or verbosity == 'verbose':
        log_level = logging.DEBUG
    if verbosity == 'warn'\
            or verbosity == 'production':
        log_level = logging.WARNING
    # print('remaining_argv={}'.format(remaining_argv))
    return log_level, remaining_argv


def send_error_and_close(message, connection):
    connection.send_obj(message)
    connection.close()


def get_path_elements(filepath):
    drive, path = os.path.splitdrive(filepath)
    # note: Don't do these two.
    # path, ext = os.path.splitext(path)
    # path = os.path.normpath(path)
    # note: a trailing slash fucks this shit up. If it's a dir, just don't leave
    # the training slash.
    dirs = []
    while(True):
        head, tail = os.path.split(path)
        if tail != '':
            dirs.append(tail)
        else:
            if head != '':
                dirs.append(head)
            break
        path = head
    dirs.reverse()
    return dirs


def get_free_space_bytes(dirname):
    """Return folder/drive free space (in megabytes)."""
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(dirname), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        st = os.statvfs(dirname)
        return st.f_bavail * st.f_frsize

# This is the value to indicate that a cloud has whatever size is left on disk
INFINITE_SIZE = -1


def get_full_cloudname(uname, cname):
    return uname + '/' + cname


def validate_cloudname(cloudname_string):
    rd = Error()
    parts = cloudname_string.split('/')
    if len(parts) == 2:
        uname = parts[0]
        cname = parts[1]
        if len(uname) > 0 and len(cname) > 0:
            rd = Success((parts[0], parts[1]))
    return rd


def is_address_ipv6(address):
    # type: (str) -> bool
    return ':' in address


def format_full_address(address='127.0.0.1', port=0, is_ipv6=None):
    # type: (str, int, bool) -> str
    if is_ipv6 is None:
        is_ipv6 = is_address_ipv6(address)
    return ('[{}]:{}' if is_ipv6 else '{}:{}').format(address, port)


class RelativePath(object):
    # Stores a relative path as a non-delimited string. Ex:
    # [0]   ./foo -> foo
    # [1]   /bar -> bar
    # [2]   who\goes\there -> who/goes/there
    # [3]   foo/../../what -> what
    # See RelativePathTests
    def __init__(self):
        self._path = None
        pass

    def from_relative(self, relative_path_string):
        """
        Use this to construct a RelativePath.
        This way, user input will be validated
        :param relative_path_string:
        :return:
        """
        working = relative_path_string

        if not os.path.isabs(working):
            working = os.path.join('/', working)
        try:
            working = os.path.relpath(working, os.path.normpath('/'))
        except ValueError, e:
            return Error(e.message)
        working = posixpath.normpath(working)

        working_elems = working.split('\\')

        working = '/'.join(working_elems)
        working = posixpath.normpath(working)
        self._path = working

        is_child = working == '.' or os.path.abspath(working).startswith(os.path.abspath('.')+os.sep)
        return ResultAndData(is_child, None)

    def to_string(self):
        return self._path

    def to_absolute(self, root):
        return os.path.join(root, self._path)
