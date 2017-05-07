import socket
from connections.RawConnection import RawConnection
from util import mylog
from connections.WebSocketConnection import MyBigFuckingLieServerProtocol, \
    WebsocketConnection
import txaio
try:
    import asyncio
except ImportError:  # Trollius >= 0.3 was renamed
    import trollius as asyncio
from autobahn.asyncio.websocket import WebSocketServerFactory
from time import sleep


class NetworkThread(object):
    def __init__(self, ip_address, host, use_ipv6=True):
        self.shutdown_requested = False
        self.server_sock = None
        self._use_ipv6 = use_ipv6
        self.ipv4_address = None
        self.ipv6_address = None
        if self._use_ipv6:
            self.ipv6_address = ip_address
        else:
            self.ipv4_address = ip_address

        self.port = host.get_instance().host_port
        self.ws_port = host.get_instance().host_ws_port

        self.setup_socket(ip_address, self._use_ipv6)
        self.connection_queue = []

        self.ws_event_loop = None
        self.ws_coro = None
        self.ws_server_protocol_instance = None
        self.ws_internal_server_socket = None
        self.ws_internal_port = self.ws_port + 1

        # This lock belongs to the Host that spawned us.
        self._host = host

        # This V is done when the ws_work_thread is started,
        #   to keep in another thread
        # self.setup_web_socket(ipv6_address)

    def setup_socket(self, ip_address, use_ipv6=True):
        if use_ipv6:
            self.server_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            failure_count = 0
            succeeded = False
            while not succeeded:
                try:
                    self.server_sock.setsockopt(socket.SOL_SOCKET,
                                                socket.SO_REUSEADDR, 1)
                    self.server_sock.bind((ip_address, self.port, 0, 0))
                    succeeded = True
                    break
                except socket.error, e:
                    failure_count += 1
                    mylog('Failed {} time(s) to bind to {}'.format(
                        failure_count, (ip_address, self.port)), '34')
                    mylog(e.message)
                    if failure_count > 4:
                        raise e
                    sleep(1)
            mylog('Bound to ipv6 address={}'.format(ip_address))
        else:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.bind((ip_address, self.port))
            mylog('Bound to ipv4 address={}'.format(ip_address))

    def setup_web_socket(self, ip_address):
        mylog('top of ws thread')
        self._make_internal_socket()
        self.ws_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.ws_event_loop)
        txaio.use_asyncio()
        txaio.start_logging()
        factory = WebSocketServerFactory(
            u"ws://[{}]:{}".format(ip_address, self.ws_port)
        )
        factory.protocol = MyBigFuckingLieServerProtocol
        MyBigFuckingLieServerProtocol.net_thread = self

        # reuse address is needed so that we can swap networks relatively
        # seamlessly. I'm not sure what side effect it may have, todo:19
        self.ws_coro = self.ws_event_loop.create_server(factory
                                                        , ip_address
                                                        , self.ws_port
                                                        , reuse_address=True)

        mylog('Bound websocket to (ip, port)=({},{})'
              .format(ip_address, self.ws_port))

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

        mylog('[-- Completed internal server in NetworkThread --]', '46')

    def work_thread(self):
        self.server_sock.listen(5)

        while not self.shutdown_requested:
            (connection, address) = self.server_sock.accept()
            # self._host.acquire_lock()
            raw_conn = RawConnection(connection)
            mylog('Connected by {}'.format(address))
            self.connection_queue.append((raw_conn, address))
            self._host.signal()
            # self._host.release_lock()

        if self.server_sock is not None:
            self.server_sock.shutdown(socket.SHUT_RDWR)

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
        if self.ws_internal_server_socket is not None:
            self.ws_internal_server_socket.close()
        if self.server_sock is not None:
            self.server_sock.close()
        mylog('Shut down server socket on {}'.format(
            self.ipv6_address if self._use_ipv6 else self.ipv4_address))

    def add_ws_conn(self, mbflsp):
        mylog('adding ws conn')

        # todo: Lock this such that only the MBFLSP that is currently connecting
        # cont    can actually accept the conn. (prevent out of order conns)
        (connection, address) = self.ws_internal_server_socket.accept()
        # self._host.acquire_lock()
        mylog('accepted connection from MBFLSP')
        ws_conn = WebsocketConnection(connection, mbflsp)
        self.connection_queue.append((ws_conn, address))
        self.signal_host()
        # self._host.release_lock()

    def signal_host(self):
        self._host.signal()

    def is_ipv6(self):
        return self._use_ipv6



