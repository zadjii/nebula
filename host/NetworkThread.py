import socket
from threading import Thread


from connections.RawConnection import RawConnection
from host.function.network_updates import filter_func
from util import mylog
from host import HOST_PORT, HOST_WS_PORT
from connections.WebSocketConnection import MyBigFuckingLieServerProtocol
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
        self.ws_server = None
        self.ws_internal_server_socket = None
        self.ws_internal_port = HOST_WS_PORT + 1
        self.setup_web_socket(ipv6_address)
        # self.setup_web_socket2(ipv6_address)

    def setup_socket(self, ipv6_address):
        self.server_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.server_sock.bind((ipv6_address, self.port, 0, 0))
        mylog('Bound to ipv6 address={}'.format(ipv6_address))

    def setup_web_socket(self, ipv6_address):
        mylog('top of ws thread')
        # self._make_internal_socket()
        self.ws_event_loop = asyncio.new_event_loop()
        # self.ws_event_loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.ws_event_loop)
        txaio.use_asyncio()
        txaio.start_logging()
        factory = WebSocketServerFactory(
            u"ws://[{}]:{}".format(ipv6_address, self.ws_port)
            # , debug=False
        )
            # u"ws://{}:{}".format(ipv6_address, self.ws_port), debug = False)
        factory.protocol = MyBigFuckingLieServerProtocol

        self.ws_coro = self.ws_event_loop.create_server(factory, ipv6_address, self.ws_port)
        # self.ws_coro = self.ws_event_loop.create_server(factory, '0.0.0.0', self.ws_port)
        mylog('Bound websocket to ipv6 address, port={},{}'
              .format(ipv6_address, self.ws_port))

    # def _make_internal_socket(self):
    #     mylog('Creating a internal server in NetworkThread')
    #     self.ws_internal_server_socket = socket.socket()
    #     mylog('NT - before bind')
    #     try:
    #         self.ws_internal_server_socket.bind(
    #             ('localhost', self.ws_internal_port))
    #         mylog('NT - \x1b[32;46mbound to {}\x1b[0m'.format(self.ws_internal_port))
    #     except Exception as e:
    #         mylog('oof i fucked up')
    #         mylog(e.message)
    #
    #     self.ws_internal_server_socket.listen(5)  # todo does this 5 make sense?
    #     mylog('  \x1b[46mCompleted internal server in NetworkThread\x1b[0m')

    def setup_web_socket2(self, ipv6_address):
        mylog('top of ws thread')
        self.ws_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.ws_event_loop)
        # txaio.use_asyncio()
        # txaio.start_logging()
        # log.startLogging(sys.stdout)
        factory = WebSocketServerFactory(
            u"ws://{}:{}".format(ipv6_address, self.ws_port)
            # , debug=False
        )
        # u"ws://{}:{}".format(ipv6_address, self.ws_port), debug = False)
        factory.protocol = MyBigFuckingLieServerProtocol

        self.ws_coro = self.ws_event_loop.create_server(factory, ipv6_address,
                                                        self.ws_port)
        self.ws_coro = self.ws_event_loop.create_server(factory, '0.0.0.0', self.ws_port)
        # reactor.listenTCP(self.ws_port, factory)
        # mylog('Bound websocket to ipv6 address, port={},{}'
        #       .format(ipv6_address, self.ws_port))

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
        print 'ws work thread'
        # reactor.run(installSignalHandlers=0)
        # mylog('im a dumbass')
        # # so I guess you run_until_complete, then run_forever? wat?
        # pass
        server = self.ws_event_loop.run_until_complete(self.ws_coro)
        mylog('\x1b[36m[36] - ws work thread started\x1b[0m')

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


