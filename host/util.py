import socket
import ssl
from datetime import datetime
__author__ = 'Mike'


def check_response(expected, recieved):
    if not(int(expected) == int(recieved)):
        raise Exception('Received wrong msg-code, expected',expected,', received',recieved)


def setup_remote_socket(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
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


def mylog(message):
    now = datetime.utcnow()
    now_string = now.strftime('%y-%m-%d %H:%M%S.') + now.strftime('%f')[0:3]
    if mylog_name is not None:
        print '{}|[{}] {}'.format(now_string, mylog_name, message)
    else:
        print '{}| {}'.format(now_string, message)


