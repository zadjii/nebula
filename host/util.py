import socket
import ssl
from datetime import datetime
__author__ = 'Mike'


def get_ipv6_list():
    """Returns all suitable (public) ipv6 addresses for this host"""
    addr_info = socket.getaddrinfo(socket.gethostname(), None)
    ipv6_addresses = []
    for iface in addr_info:
        if iface[0] == socket.AF_INET6:
            if iface[4][3] == 0: # if the zoneid is 0, indicating global ipv6
                ipv6_addresses.append(iface[4])
    return [ipaddr[0] for ipaddr in ipv6_addresses]


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


