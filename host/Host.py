import sys
from connections.WebSocketConnection import MyBigFuckingLieServerProtocol
from connections.RawConnection import RawConnection
from host import HOST_WS_HOST, HOST_WS_PORT, get_db
from host.NetworkThread import NetworkThread
from host.function.dbg_nodes import dbg_nodes
from host.models import Cloud
from host.util import set_mylog_name, mylog, get_ipv6_list, setup_remote_socket
from messages.HostHandshakeMessage import  HostHandshakeMessage
__author__ = 'Mike'
from threading import Thread

from host.function.mirror import mirror
from host.function.tree import db_tree, tree
from host.function.list_clouds import list_clouds
from host.function.local_updates import local_update_thread
from host.function.network_updates import receive_updates_thread

try:
    import asyncio
except ImportError:  # Trollius >= 0.3 was renamed
    import trollius as asyncio
from autobahn.asyncio.websocket import WebSocketServerFactory


class Host:
    def __init__(self):
        self.active_network_obj = None
        self.active_network_thread = None
        self.active_ws_thread = None

    def start(self, argv):
        set_mylog_name('nebs')
        # todo process start() args here

        ipv6_addresses = get_ipv6_list()
        if len(ipv6_addresses) < 1:
            mylog('Could\'nt acquire an IPv6 address')
        else:
            self.spawn_net_thread(ipv6_addresses[0])
            # local_update thread will handle the first handshake/host setup

        ###############
        # FIXME: Add WS support back
        # ws_thread = Thread(target=ws_thread_function, args=argv)
        # ws_thread.start()

        ###############
        try:
            self.do_local_updates()
        finally:
            self.shutdown()

        print 'Both the local update checking thread and the network thread have exited.'

    def do_local_updates(self):
        local_update_thread(self)

    def spawn_net_thread(self, ipv6_address):
        if self.active_network_obj is not None:
            self.active_network_obj.shutdown()
        mylog('Spawning new server thread on {}'.format(ipv6_address))
        self.active_network_obj = NetworkThread(ipv6_address)
        self.active_network_thread = Thread(
            target=self.active_network_obj.work_thread, args=[]
        )
        self.active_network_thread.start()

    def active_ipv6(self):
        if self.active_network_obj is not None:
            return self.active_network_obj.ipv6_address
        else:
            return None

    def shutdown(self):
        if self.active_network_obj is not None:
            self.active_network_obj.shutdown()

    def change_ip(self, new_ip, clouds):
        if new_ip is None:
            mylog('I should tell all the remotes that I\'m dead now.')  # fixme
            # at this point, how is my active net thread connected to anything?
            if self.active_network_obj is not None:
                self.active_network_obj.shutdown()
        else:
            self.spawn_net_thread(new_ip)
            for cloud in clouds:
                self.send_remote_handshake(cloud)

    def send_remote_handshake(self, cloud):
        mylog('Telling {}\'s remote that [{}]\'s at {}'.format(
            cloud.name, cloud.my_id_from_remote, self.active_ipv6())
        )
        remote_sock = setup_remote_socket(cloud.remote_host, cloud.remote_port)
        remote_conn = RawConnection(remote_sock)
        msg = HostHandshakeMessage(
            cloud.my_id_from_remote,
            self.active_network_obj.ipv6_address,
            self.active_network_obj.port,
            0,  # todo fill in ws port
            0  # todo update number/timestamp? it's in my notes
        )
        remote_conn.send_obj(msg)
        # todo
        # response = remote_conn.recv_obj()
        remote_conn.close()


def ws_thread_function(argv):
    mylog('top of ws thread')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    factory = WebSocketServerFactory(u"ws://{}:{}".format(HOST_WS_HOST, HOST_WS_PORT), debug=False)
    factory.protocol = MyBigFuckingLieServerProtocol

    # loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '0.0.0.0', HOST_WS_PORT)
    mylog('\x1b[35m[35]\x1b[0m')
    server = loop.run_until_complete(coro)
    mylog('\x1b[36m[36]\x1b[0m')

    try:
        loop.run_forever()
        mylog('after run_forever for shits')
    except KeyboardInterrupt:
        pass
    finally:
        mylog('\x1b[36mTHIS IS BAD\x1b[0m')
        mylog('\x1b[35mTHIS IS BAD\x1b[0m')
        mylog('\x1b[34mTHIS IS BAD\x1b[0m')
        mylog('\x1b[33mTHIS IS BAD\x1b[0m')
        server.close()
        loop.close()


def start(argv):
    host_controller = Host()
    host_controller.start(argv=argv)


def old_start(argv):
    set_mylog_name('nebs')
    # todo process start() args here
    # local_thread = Thread(target=local_update_thread, args=argv)
    network_thread = Thread(target=receive_updates_thread, args=argv)
    # local_thread.start()
    network_thread.start()

    ###############

    ws_thread = Thread(target=ws_thread_function, args=argv)
    ws_thread.start()

    ###############
    local_update_thread()
    # local_thread.join()
    # network_thread.join()
    print 'Both the local update checking thread and the network thread have exited.'


commands = {
    'mirror': mirror
    , 'start': start
    , 'list-clouds': list_clouds
    , 'tree': tree
    , 'db-tree': db_tree
    , 'dbg-nodes': dbg_nodes
}
command_descriptions = {
    'mirror': '\t\tmirror a remote cloud to this device'
    , 'start': '\t\tstart the main thread checking for updates'
    , 'list-clouds': '\tlist all current clouds'
    , 'tree': '\t\tdisplays the file structure of a cloud on this host.'
    , 'db-tree': '\tdisplays the db structure of a cloud on this host.'
}


def usage(argv):
    print 'usage: nebs <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]


def nebs_main(argv):
    # if there weren't any args, print the usage and return
    if len(argv) < 2:
        usage(argv)
        sys.exit(0)

    command = argv[1]

    selected = commands.get(command, usage)
    selected(argv[2:])
    sys.exit(0)


if __name__ == '__main__':
    nebs_main(sys.argv)
