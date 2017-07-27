import ctypes
import os
import platform
from logging import *
import logging.handlers
from os import path
from datetime import datetime
###############################################################################
import sys

NEBULA_ROOT = path.abspath(path.dirname(__file__))
INSTANCES_ROOT = path.abspath(path.join(NEBULA_ROOT, './instances'))


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
    # print _log, _log.name, _log.handlers
    return _log


def config_logger(name='nebula', filename=None, level=logging.INFO):
    global _log
    # print _log
    if _log is not None:
        return
    _log = getLogger(name)
    # print _log
    # print _log.handlers
    for h in _log.handlers:
        _log.removeHandler(h)
    # print _log.handlers
    if filename is None:
        # hdlr = logging.StreamHandler(sys.stdout)
        hdlr = logging.StreamHandler()
    else:
        hdlr = logging.handlers.RotatingFileHandler(
                filename, maxBytes=100*1024*1024, backupCount=5)
    # hdlr.setLevel(level)
    _log.setLevel(level)
    formatter = logging.Formatter('%(asctime)s|[%(name)s](%(levelname)s) %(message)s')
    hdlr.setFormatter(formatter)
    _log.addHandler(hdlr)
    # print _log.handlers
    # print _log
    # print _log.name
    # print 'config_logger'



# class Mylog(object):
#     def __init__(self):
#         self._log_name = None
#         self._log_file = None
#         self._log_file_handler = None
#         self._log_level = DEBUG
#         self._log = getLogger('nebula')
#         self._log.setLevel(DEBUG)
#         # logging.basicConfig(format='%(asctime)s%(message)s', stream=sys.stdout)
#         # logging.basicConfig(format='%(asctime)s', stream=sys.stdout)
#         # logging.basicConfig(format='%(message)s', stream=sys.stdout)
#         # logging.basicConfig(format='%(message)s')
#
#     def construct_message(self, message, sgr_seq='0'):
#         # now = datetime.utcnow()
#         # now_string = now.strftime('%y%m-%d %H:%M:%S.') + now.strftime('%f')[0:2]
#         # output = '{}|'.format(now_string)
#         output = '|'
#         if self._log_name is not None:
#             output += '[{}]'.format(self._log_name)
#         output += ' '
#
#         use_sgr = sgr_seq is not '0' and not self.using_file()
#         if use_sgr:
#             output += '\x1b[{}m'.format(sgr_seq)
#         output += str(message)
#         if use_sgr:
#             output += '\x1b[0m'
#
#         return output
#
#     def mylog(self, message, sgr_seq='0'):
#         # output = self.construct_message(message, sgr_seq)
#         output = message
#         self.info(output)
#
#     def debug(self, message):
#         self._log.debug(message)
#
#     def info(self, message):
#         self._log.info(message)
#
#     def warn(self, message):
#         self._log.warning(message)
#
#     def error(self, message):
#         self._log.error(message)
#
#     def set_name(self, log_name):
#         self._log_name = log_name
#         # _old_file = self._log_file
#         # _old_handler = self._log_file_handler
#         # self.set_file(None)
#         #
#
#     def set_file(self, log_file):
#         self._log_file = log_file
#         if self._log_file_handler is not None:
#             self._log.removeHandler(self._log_file_handler)
#         if log_file is not None:
#             self._log_file_handler = logging.handlers.RotatingFileHandler(
#                 self._log_file, maxBytes=100*1024*1024, backupCount=5)
#             self._log.addHandler(self._log_file_handler)
#             logging.basicConfig(stream=None)
#
#     def using_file(self):
#         return self._log_file is not None
#
#     def set_level(self, verbosity):
#         self._log.setLevel(verbosity)


mylog_name = None
mylog_file = None

# mlog = Mylog()

def set_mylog_name(name):
    # global mylog_name
    # mylog_name = name
    # mlog.set_name(name)
    pass

def set_mylog_file(filename):
    # global mylog_file
    # mylog_file = filename
    # mlog.set_file(filename)
    pass

def mylog(message, sgr_seq='0'):
    # mlog.mylog(message, sgr_seq)
    # global _log
    __log = get_mylog()
    if not __log:
        print 'Fool! You have\'nt configured the log yet!'
        print message
        return
    # print __name__, __log, message

    __log.info(message)



    # now = datetime.utcnow()
    # now_string = now.strftime('%y%m-%d %H:%M:%S.') + now.strftime('%f')[0:2]
    # use_sgr = sgr_seq is not '0' and mylog_file is None
    # output = '{}|'.format(now_string)
    # if mylog_name is not None:
    #     output += '[{}]'.format(mylog_name)
    # output += ' '
    # if use_sgr:
    #     output += '\x1b[{}m'.format(sgr_seq)
    # output += str(message)
    # if use_sgr:
    #     output += '\x1b[0m'
    #
    # # if mylog_name is not None:
    # #     message = '{}|[{}] \x1b[{}m{}\x1b[0m'.format(now_string, mylog_name, sgr_seq, message)
    # # else:
    # #     message = '{}| \x1b[{}m{}\x1b[0m'.format(now_string, sgr_seq, message)
    # if mylog_file is not None:
    #     with open(mylog_file, mode='a') as handle:
    #         handle.write(output + '\n')
    # else:
    #     print(output)


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


def validate_cloudname(cloudname_string):
    rd = Error()
    parts = cloudname_string.split('/')
    if len(parts) == 2:
        uname = parts[0]
        cname = parts[1]
        if len(uname) > 0 and len(cname) > 0:
            rd = Success((parts[0], parts[1]))
    return rd
