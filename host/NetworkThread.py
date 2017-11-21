import socket
import ssl
from common_util import *
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
    def __init__(self, external_ip, internal_ip, host):
        # type: (str, str, HostController) -> NetworkThread
        self._use_ipv6 = ':' in external_ip
        self.shutdown_requested = False
        self.server_sock = None  # This is the local socket for the TCP server
        self._ws_sock = None  # This is the local socket for the WS server
        self._external_ip = external_ip
        self._internal_ip = internal_ip

        # These may all be 0 - indicating that they should be bound to whatever's open.
        # When binding, ALWAYS get the real port back from the socket.
        # These are the "internal" ports that we're actually bound to -
        #    We may map to a different port on the upnp layer.

        self._port = host.get_instance().host_port
        self._ws_port = host.get_instance().host_ws_port
        # This however isn't going to have an external component, ever.
        self._ws_internal_port = host.get_instance().host_internal_port

        self._external_port = None
        self._external_ws_port = None

        self.connection_queue = []

        self.ws_event_loop = None
        self.ws_coro = None
        self.ws_server_protocol_instance = None
        self.ws_internal_server_socket = None

        # This lock belongs to the Host that spawned us.
        self._host = host
        mylog('[1]NetworkThread._host={}'.format(self._host))

        self.setup_socket()

        # This V is done when the ws_work_thread is started,
        #   to keep in another thread
        # self.setup_web_socket(ipv6_address)

    def setup_socket(self):
        sock_type = socket.AF_INET6 if self._use_ipv6 else socket.AF_INET
        sock_addr = (self._internal_ip, self._port, 0, 0) if self._use_ipv6 else (self._internal_ip, self._port)
        self.server_sock = socket.socket(sock_type, socket.SOCK_STREAM)
        failure_count = 0
        succeeded = False
        while not succeeded:
            try:
                self.server_sock.setsockopt(socket.SOL_SOCKET,
                                            socket.SO_REUSEADDR, 1)
                self.server_sock.bind(sock_addr)
                succeeded = True
                self._port = self.server_sock.getsockname()[1]
                mylog('[2]NetworkThread._host={}'.format(self._host))

                rd = self._host.get_net_controller().create_port_mapping(self._port)
                if rd.success:
                    self._external_port = rd.data
                    self._host.get_instance().persist_ip(self._external_ip)
                    self._host.get_instance().persist_port(self._external_port)
                else:
                    raise Exception(rd.data)
                break
            except socket.error, e:
                failure_count += 1
                mylog('Failed {} time(s) to bind to {}'.format(
                    failure_count, sock_addr), '34')
                mylog(e.message)
                if failure_count > 4:
                    self.shutdown()
                    raise e
                sleep(1)
        mylog('Bound to ip address={}'.format(self._internal_ip))

    def setup_web_socket(self):
        # type: (str) -> ResultAndData
        _log = get_mylog()
        _log.debug('top of ws thread')
        host_instance = self._host.get_instance()
        rd = self._make_internal_socket()
        if rd.success:
            self.ws_event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.ws_event_loop)
            txaio.use_asyncio()
            txaio.start_logging()
            factory = WebSocketServerFactory(
                u"ws://[{}]:{}".format(self._external_ip, self._ws_port)
            )
            factory.protocol = MyBigFuckingLieServerProtocol
            # fixme woah this seems terrible
            # is this a class static value that's being set to this instance? yikes
            MyBigFuckingLieServerProtocol.net_thread = self

            # Create a socket for the event loop to use:
            sock_type = socket.AF_INET6 if self._use_ipv6 else socket.AF_INET
            sock_addr = (self._internal_ip, self._ws_port, 0, 0) if self._use_ipv6 else (self._internal_ip, self._ws_port)
            self._ws_sock = socket.socket(sock_type, socket.SOCK_STREAM)
            failure_count = 0
            succeeded = False
            while not succeeded:
                try:
                    self._ws_sock.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                    self._ws_sock.bind(sock_addr)
                    succeeded = True
                    self._ws_port = self._ws_sock.getsockname()[1]
                    rd = self._host.get_net_controller().create_port_mapping(self._ws_port)
                    if rd.success:
                        self._external_ws_port = rd.data
                    else:
                        raise Exception(rd.data)
                    break
                except socket.error, e:
                    failure_count += 1
                    mylog('Failed {} time(s) to bind to {}'.format(
                        failure_count, sock_addr), '34')
                    mylog(e.message)
                    if failure_count > 4:
                        self.shutdown()
                        raise e
                    sleep(1)

            # reuse address is needed so that we can swap networks relatively
            # seamlessly. I'm not sure what side effect it may have, todo:19

            sslcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            sslcontext.load_cert_chain(host_instance.cert_file, host_instance.key_file)

            self.ws_coro = self.ws_event_loop.create_server(factory
                                                            , host=None, port=None
                                                            , sock=self._ws_sock
                                                            , ssl=sslcontext
                                                            , reuse_address=True)

            mylog('Bound websocket to (ip, port)=({},{})'
                  .format(self._internal_ip, self._ws_port))

        if not rd.success:
            mylog('Failed to create a websocket.')

        return rd

    def _make_internal_socket(self):
        # type: () -> ResultAndData
        """Creates the internal server socket that accepts connections from
        MBFLSP. These connections are then added to the connection_queue.
        MBFLSP talks to the world over :34567
        MBFLSP forwards these messages internally from :* to :34568
        the internal_socket accepts the conn from :*, creates a
            WebsocketConnection to wrap the connection, then adds to the queue
        The main thread then pops the connection off, and processes it.
        """
        mylog('Creating a internal server in NetworkThread...')
        self.ws_internal_server_socket = socket.socket()
        mylog('NT - before bind')

        failures = 0
        rd = Error()
        while True:
            try:
                self.ws_internal_server_socket.bind(
                    ('localhost', self._ws_internal_port))
                self._ws_internal_port = self.ws_internal_server_socket.getsockname()[1]
                mylog('Successfully bound internal server socket on {}'.format(
                    self._ws_internal_port), '32;46')
                rd = Success()
                break
            except Exception as e:
                mylog('Failed binding internal server socket on {}'.format(
                    self._ws_internal_port), '31;103')
                mylog(e.message)
                failures += 1
                if failures > 4:
                    break
                mylog('Retrying...')
                sleep(1)
        if rd.success:
            mylog('[-- Completed internal server in NetworkThread --]', '46')
        return rd

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
        try:
            rd = self.setup_web_socket()
        except Exception, e:
            self.shutdown()
            raise e
        if not rd.success:
            mylog('Failed to setup websocket. Shutting down host.')
            self._host.shutdown()
            return

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
        mylog('Shut down server socket on {}->{}'.format(
            self._external_ip, self._internal_ip))

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

    def get_external_ip(self):
        return self._external_ip

    def get_external_port(self):
        return self._external_port

    def get_external_ws_port(self):
        return self._external_ws_port
