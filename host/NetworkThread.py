import socket
from threading import Thread

from connections.RawConnection import RawConnection
from host.function.network_updates import filter_func
from util import mylog
from host import HOST_PORT


class NetworkThread(object):
    def __init__(self, ipv6_address):
        self.shutdown_requested = False
        self.server_sock = None
        self.ipv6_address = ipv6_address
        self.port = HOST_PORT
        self.setup_socket(ipv6_address)

    def setup_socket(self, ipv6_address):
        self.server_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.server_sock.bind((ipv6_address, self.port, 0, 0))
        mylog('Bound to ipv6 address={}'.format(ipv6_address))

    def work_thread(self):
        self.server_sock.listen(5)
        while not self.shutdown_requested:
            (connection, address) = self.server_sock.accept()
            raw_conn = RawConnection(connection)
            mylog('Connected by {}'.format(address))
            thread = Thread(target=filter_func, args=[raw_conn, address])
            thread.start()
            thread.join()
        self.server_sock.shutdown()
        mylog('Shut down server socket on {}'.format(self.ipv6_address))

    def shutdown(self):
        self.shutdown_requested = True


