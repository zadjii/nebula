import ctypes
import os
import platform
from os import path
from datetime import datetime
###############################################################################
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

mylog_name = None
mylog_file = None

def set_mylog_name(name):
    global mylog_name
    mylog_name = name

def set_mylog_file(filename):
    global mylog_file
    mylog_file = filename

def mylog(message, sgr_seq='0'):
    now = datetime.utcnow()
    now_string = now.strftime('%y%m-%d %H:%M:%S.') + now.strftime('%f')[0:2]
    use_sgr = sgr_seq is not '0' and mylog_file is None
    output = '{}|'.format(now_string)
    if mylog_name is not None:
        output += '[{}]'.forma(mylog_name)
    output += ' '
    if use_sgr:
        output += '\x1b[{}m'.format(sgr_seq)
    output += message
    if use_sgr:
        output += '\x1b[0m'
        
    # if mylog_name is not None:
    #     message = '{}|[{}] \x1b[{}m{}\x1b[0m'.format(now_string, mylog_name, sgr_seq, message)
    # else:
    #     message = '{}| \x1b[{}m{}\x1b[0m'.format(now_string, sgr_seq, message)
    if mylog_file is not None:
        with open(mylog_file, mode='a') as handle:
            handle.write(message + '\n')
    else:
        print(message)


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


