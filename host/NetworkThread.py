import socket
from threading import Thread


from connections.RawConnection import RawConnection
from host.function.network_updates import filter_func
from util import mylog
from host import HOST_PORT, HOST_WS_PORT
from connections.WebSocketConnection import MyBigFuckingLieServerProtocol, \
    WebsocketConnection
#
import txaio
try:
    import asyncio
except ImportError:  # Trollius >= 0.3 was renamed
    import trollius as asyncio
from autobahn.asyncio.websocket import WebSocketServerFactory
# import sys
#
# from twisted.python import log
# from twisted.internet import reactor
# from autobahn.twisted.websocket import WebSocketServerFactory


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
        self.ws_server_protocol_instance = None
        self.ws_internal_server_socket = None
        self.ws_internal_port = HOST_WS_PORT + 1
        # self.setup_web_socket(ipv6_address)

    def setup_socket(self, ipv6_address):
        self.server_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.server_sock.bind((ipv6_address, self.port, 0, 0))
        mylog('Bound to ipv6 address={}'.format(ipv6_address))

    def setup_web_socket(self, ipv6_address):
        mylog('top of ws thread')
        self._make_internal_socket()
        self.ws_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.ws_event_loop)
        txaio.use_asyncio()
        txaio.start_logging()
        factory = WebSocketServerFactory(
            u"ws://[{}]:{}".format(ipv6_address, self.ws_port)
        )
        factory.protocol = MyBigFuckingLieServerProtocol
        MyBigFuckingLieServerProtocol.net_thread = self

        self.ws_coro = self.ws_event_loop.create_server(factory, ipv6_address, self.ws_port)
        mylog('Bound websocket to (ipv6, port)=({},{})'
              .format(ipv6_address, self.ws_port))

    def _make_internal_socket(self):
        """Creates the internal server socket that accepts connections from
        MBFLSP. These connections are then added to the connection_queue.
        MBFLSP talks to the world over :34567
        MBFLSP forwards these messages internally from :* to :34568
        the internal_socket accepts the conn from :*, creates a
            WebsocketConnection to wrap the connection, then adds to the queue
        The main thread then pops the connection off, and processes it.
        """
        mylog('Creating a internal server in NetworkThread')
        self.ws_internal_server_socket = socket.socket()
        mylog('NT - before bind')
        try:
            self.ws_internal_server_socket.bind(
                ('localhost', self.ws_internal_port))
            mylog('NT - bound to {}'.format(self.ws_internal_port), '32;46')
        except Exception as e:
            mylog('oof i fucked up')
            mylog(e.message)

        mylog('  \x1b[46mCompleted internal server in NetworkThread\x1b[0m')

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
        self.setup_web_socket(self.ipv6_address)
        self.ws_internal_server_socket.listen(5)

        mylog('ws work thread - 0')

        server = self.ws_event_loop.run_until_complete(self.ws_coro)
        mylog('[36] - ws work thread started', '36')

        try:
            mylog('ws - before run_forever')
            self.ws_event_loop.run_forever()
            mylog('ws run forever exited, ws server stopping')
        except KeyboardInterrupt:
            pass
        finally:
            mylog('THIS IS (not so) BAD', '36')
            mylog('THIS IS (not so) BAD', '35')
            mylog('THIS IS (not so) BAD', '34')
            mylog('THIS IS (not so) BAD', '33')
            server.close()
            self.ws_event_loop.close()

    def shutdown(self):
        self.shutdown_requested = True
        if self.ws_event_loop is not None:
            self.ws_event_loop.stop()

    def add_ws_conn(self, mbflsp):
        mylog('adding ws conn')
        # todo: Lock this such that only the MBFLSP that is currently connecting
        # cont    can actually accept the conn. (prevent out of order conns)
        (connection, address) = self.ws_internal_server_socket.accept()
        ws_conn = WebsocketConnection(connection, mbflsp)
        self.connection_queue.append((ws_conn, address))


