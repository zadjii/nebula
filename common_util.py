import os
from datetime import datetime

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

def set_mylog_name(name):
    global mylog_name
    mylog_name = name


def mylog(message, sgr_seq='0'):
    now = datetime.utcnow()
    now_string = now.strftime('%y%m-%d %H:%M:%S.') + now.strftime('%f')[0:2]
    if mylog_name is not None:
        print '{}|[{}] \x1b[{}m{}\x1b[0m'.format(now_string, mylog_name, sgr_seq, message)
    else:
        print '{}| \x1b[{}m{}\x1b[0m'.format(now_string, sgr_seq, message)


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
