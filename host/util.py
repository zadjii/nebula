import os
import socket
import ssl
from datetime import datetime

from host import Cloud
from msg_codes import send_generic_error_and_close

__author__ = 'Mike'

###############################################################################
from collections import namedtuple
ResultAndData = namedtuple('ResultAndData', 'success, data')
def ERROR(data=None):
    return ResultAndData(False, data)
###############################################################################


def validate_host_id(db, host_id, conn):
    rd = get_matching_clouds(db, host_id)
    if not rd.success:
        send_generic_error_and_close(conn)
        raise Exception(rd.data)
    return rd


def get_matching_clouds(db, host_id):
    rd = ERROR()
    matching_id_clouds = db.session.query(Cloud)\
        .filter(Cloud.my_id_from_remote == host_id)

    if matching_id_clouds.count() <= 0:
        rd = ERROR('Received a message intended for id={},'
                   ' but I don\'t have any clouds with that id'
                   .format(host_id))
    else:
        rd = ResultAndData(True, matching_id_clouds)
    return rd


def get_ipv6_list():
    """Returns all suitable (public) ipv6 addresses for this host"""
    addr_info = socket.getaddrinfo(socket.gethostname(), None)
    ipv6_addresses = []
    for iface in addr_info:
        if iface[0] == socket.AF_INET6:
            if iface[4][3] == 0: # if the zoneid is 0, indicating global ipv6
                ipv6_addresses.append(iface[4])
    valid_global_ipv6s = [ipaddr[0] for ipaddr in ipv6_addresses]
    if (len(valid_global_ipv6s)) == 0:
        valid_global_ipv6s = ['::1']  # FIXME wow I shouldn't have to explain why this is bad.
    return valid_global_ipv6s


def check_response(expected, recieved):
    if not(int(expected) == int(recieved)):
        raise Exception('Received wrong msg-code, expected',expected,', received',recieved)


def setup_remote_socket(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    # ipv6: 
    # s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    # s.connect((host, port, 0, 0))
    # s.create_connection((host, port))
    # TODO May want to use:
    # socket.create_connection(address[, timeout[, source_address]])
    # cont  instead, where address is a (host,port) tuple. It'll try and
    # cont  auto-resolve? which would be dope.
    sslSocket = ssl.wrap_socket(s)
    return sslSocket

mylog_name = None


def set_mylog_name(name):
    global mylog_name
    mylog_name = name


def mylog(message, sgr_seq='0'):
    now = datetime.utcnow()
    now_string = now.strftime('%y-%m-%d %H:%M%S.') + now.strftime('%f')[0:3]
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