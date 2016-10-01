import collections
import os
import signal
import sys
from threading import Thread

from connections.RawConnection import RawConnection
from host import get_db
from host.NetworkThread import NetworkThread
from host.PrivateData import PrivateData
from host.function.local_updates import local_update_thread
from host.function.network_updates import filter_func
from host.models.Cloud import Cloud
from host.util import set_mylog_name, mylog, get_ipv6_list, setup_remote_socket
from messages.HostHandshakeMessage import  HostHandshakeMessage
import platform

__author__ = 'Mike'


class Host:
    def __init__(self):
        self.active_network_obj = None
        self.active_network_thread = None
        self.active_ws_thread = None
        self.network_queue = []  # all the queued connections to handle.
        self._shutdown_requested = False
        self._local_update_thread = None
        self._private_data = {} # cloud.my_id_from_remote -> PrivateData mapping
        # self._private_data = collections.MutableMapping()

    def start(self, argv):
        set_mylog_name('nebs')
        # todo process start() args here

        # read in all the .nebs
        db = get_db()
        for cloud in db.session.query(Cloud).all():
            self.load_private_data(cloud)

        # if the mirror was completed before we started, great. We add their
        # .nebs at launch, no problem.
        # what if we complete mirroring while we're running?
        #   regardless if it has a .nebs (existing) or not (new/1st mirror)

        ipv6_addresses = get_ipv6_list()
        if len(ipv6_addresses) < 1:
            mylog('Could\'nt acquire an IPv6 address')
        else:
            self.spawn_net_thread(ipv6_addresses[0])
            # local_update thread will handle the first handshake/host setup

        try:
            self.do_local_updates()
        finally:
            self.shutdown()

        mylog('Both the local update checking thread and the network thread'
              ' have exited.')
        sys.exit()

    def do_local_updates(self):
        # signal.signal(signal.CTRL_C_EVENT, self.shutdown())
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        # local_update_thread(self)
        self._local_update_thread = Thread(
            target=local_update_thread, args=[self]
        )
        self._local_update_thread.start()
        self._local_update_thread.join()

    def spawn_net_thread(self, ipv6_address):
        if self.active_network_obj is not None:
            # todo make sure connections from the old thread get dequeue'd
            self.active_network_obj.shutdown()
        mylog('Spawning new server thread on {}'.format(ipv6_address))
        self.active_network_obj = NetworkThread(ipv6_address)
        # mylog('')
        self.active_network_thread = Thread(
            target=self.active_network_obj.work_thread, args=[]
        )
        self.active_network_thread.start()

        self.active_ws_thread = Thread(
            target=self.active_network_obj.ws_work_thread, args=[]
        )
        self.active_ws_thread.start()

    def active_ipv6(self):
        if self.active_network_obj is not None:
            return self.active_network_obj.ipv6_address
        else:
            return None

    def is_shutdown_requested(self):
        return self._shutdown_requested

    def shutdown(self):
        self._shutdown_requested = True
        if self.active_network_obj is not None:
            self.active_network_obj.shutdown()
        if self._local_update_thread is not None:
            self._local_update_thread.join()

    def change_ip(self, new_ip, clouds):
        if new_ip is None:
            if self.active_ipv6() is not None:
                mylog('I should tell all the remotes that I\'m dead now.')  # fixme
                mylog('DISCONNECTED FROM IPv6')  # fixme
            # at this point, how is my active net thread connected to anything?
            if self.active_network_obj is not None:
                self.active_network_obj.shutdown()
        else:
            self.spawn_net_thread(new_ip)
            for cloud in clouds:
                self.send_remote_handshake(cloud)

    def handshake_clouds(self, clouds):
        mylog('Telling {}\'s remote that {}\'s at {}'.format(
            [cloud.name for cloud in clouds]
            , [cloud.my_id_from_remote for cloud in clouds]
            , self.active_ipv6())
        )
        for cloud in clouds:
            self.send_remote_handshake(cloud)

    def send_remote_handshake(self, cloud):
        # mylog('Telling {}\'s remote that [{}]\'s at {}'.format(
        #     cloud.name, cloud.my_id_from_remote, self.active_ipv6())
        # )
        remote_sock = setup_remote_socket(cloud.remote_host, cloud.remote_port)
        remote_conn = RawConnection(remote_sock)
        msg = HostHandshakeMessage(
            cloud.my_id_from_remote,
            self.active_network_obj.ipv6_address,
            self.active_network_obj.port,
            self.active_network_obj.ws_port,
            0,  # todo update number/timestamp? it's in my notes
            platform.uname()[1]  # hostname
        )
        remote_conn.send_obj(msg)
        # todo
        # response = remote_conn.recv_obj()
        remote_conn.close()

    def process_connections(self):
        num_conns = len(self.active_network_obj.connection_queue)
        while num_conns > 0:
            (conn, addr) = self.active_network_obj.connection_queue.pop(0)
        # for (conn, addr) in self.active_network_obj.connection_queue[:]:
            filter_func(conn, addr)
            num_conns -= 1
            mylog('processed {} from {}'.format(conn.__class__, addr))

    def is_ipv6(self):
        return self.active_network_obj.is_ipv6()

    def has_private_data(self, cloud):
        return cloud.my_id_from_remote in self._private_data

    def get_private_data(self, cloud):
        if self.has_private_data(cloud):
            return self._private_data[cloud.my_id_from_remote]
        return None

    def load_private_data(self, cloud):
        """
        Doesn't create duplicate data for existing PrivateData
        :param cloud:
        :return:
        """
        if not self.has_private_data(cloud):
            # the PrivateData ctor reads existing ones, or creates new ones.
            if cloud.completed_mirroring:
                self._private_data[cloud.my_id_from_remote] = PrivateData(cloud)

    def reload_private_data(self, cloud):
        """
        Updates the PrivateData for this cloud. If it already exists, replaces it.
        :param cloud:
        :return:
        """
        # the PrivateData ctor reads existing ones, or creates new ones.
        if cloud.completed_mirroring:
            self._private_data[cloud.my_id_from_remote] = PrivateData(cloud)

    def is_private_data_file(self, path, cloud=None):
        if cloud is None:
            # todo: this is pretty untested. Write some tests that make sure
            db = get_db()
            for cloud2 in db.session.query(Cloud).all():
                if cloud2.root_directory == os.path.commonprefix(cloud2.root_directory, path):
                    cloud = cloud2
                    break
        if cloud is None:
            return None
        return os.path.join(cloud.root_directory, '.nebs') == path

