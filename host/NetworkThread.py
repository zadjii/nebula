import socket
from threading import Thread

from connections.RawConnection import RawConnection
from host.function.network_updates import filter_func
from util import mylog
from host import HOST_PORT, HOST_WS_PORT
from connections.WebSocketConnection import MyBigFuckingLieServerProtocol

try:
    import asyncio
except ImportError:  # Trollius >= 0.3 was renamed
    import trollius as asyncio
from autobahn.asyncio.websocket import WebSocketServerFactory


class NetworkThread(object):
    def __init__(self, ipv6_address):
        self.shutdown_requested = False
        self.server_sock = None
        self.ipv6_address = ipv6_address
        self.port = HOST_PORT
        self.ws_port = HOST_WS_PORT
        self.setup_socket(ipv6_address)
        self.connection_queue = []

        self.ws_event_loop = None
        self.ws_coro = None
        self.ws_server = None
        self.setup_web_socket(ipv6_address)

    def setup_socket(self, ipv6_address):
        self.server_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.server_sock.bind((ipv6_address, self.port, 0, 0))
        mylog('Bound to ipv6 address={}'.format(ipv6_address))

    def setup_web_socket(self, ipv6_address):
        mylog('top of ws thread')
        self.ws_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.ws_event_loop)

        factory = WebSocketServerFactory(
            u"ws://{}:{}".format(ipv6_address, self.ws_port), debug=False)
        factory.protocol = MyBigFuckingLieServerProtocol

        self.ws_coro = self.ws_event_loop.create_server(factory, ipv6_address, self.ws_port)
        mylog('Bound websocket to ipv6 address, port={},{}'
              .format(ipv6_address, self.ws_port))

    def work_thread(self):
        self.server_sock.listen(5)

        while not self.shutdown_requested:
            (connection, address) = self.server_sock.accept()
            raw_conn = RawConnection(connection)
            mylog('Connected by {}'.format(address))
            self.connection_queue.append((raw_conn, address))

        self.server_sock.shutdown(socket.SHUT_RDWR)
        mylog('Shut down server socket on {}'.format(self.ipv6_address))

    def ws_work_thread(self):
        # so I guess you run_until_complete, then run_forever? wat?
        server = self.ws_event_loop.run_until_complete(self.ws_coro)
        mylog('\x1b[36m[36]\x1b[0m')

        try:
            self.ws_event_loop.run_forever()
            mylog('ws run forever exited, ws server stopping')
        except KeyboardInterrupt:
            pass
        finally:
            mylog('\x1b[36mTHIS IS (not so) BAD\x1b[0m')
            mylog('\x1b[35mTHIS IS (not so) BAD\x1b[0m')
            mylog('\x1b[34mTHIS IS (not so) BAD\x1b[0m')
            mylog('\x1b[33mTHIS IS (not so) BAD\x1b[0m')
            server.close()
            self.ws_event_loop.close()

    def shutdown(self):
        self.shutdown_requested = True
        if self.ws_event_loop is not None:
            self.ws_event_loop.stop()


