import collections
import os
import signal
import sys
from inspect import getframeinfo, currentframe
from threading import Thread, Event, Lock, Semaphore

from common_util import mylog, ResultAndData
from connections.RawConnection import RawConnection
from host.NetworkThread import NetworkThread
from host.PrivateData import PrivateData, NO_ACCESS, READ_ACCESS
from host.WatchdogThread import WatchdogWorker
from host.function.local_updates import local_update_thread, new_main_thread
from host.function.network.client import list_files_handler, \
    handle_recv_file_from_client, handle_read_file_request, \
    handle_client_add_owner, handle_client_add_contributor
from host.function.network_updates import handle_fetch, handle_file_change, \
    handle_remove_file
from host.models.Cloud import Cloud
from host.util import set_mylog_name, mylog, get_ipv6_list, setup_remote_socket, \
    get_client_session, permissions_are_sufficient
from messages.RefreshMessageMessage import RefreshMessageMessage
from messages import InvalidPermissionsMessage
from messages.HostHandshakeMessage import  HostHandshakeMessage
import platform

from msg_codes import HOST_HOST_FETCH, HOST_FILE_PUSH, REMOVE_FILE, \
    STAT_FILE_REQUEST, LIST_FILES_REQUEST, CLIENT_FILE_PUT, READ_FILE_REQUEST, \
    CLIENT_ADD_OWNER, CLIENT_ADD_CONTRIBUTOR, REFRESH_MESSAGE

__author__ = 'Mike'


class HostController:
    def __init__(self, nebs_instance):
        self.active_network_obj = None
        self.active_network_thread = None
        self.active_ws_thread = None
        self.network_queue = []  # all the queued connections to handle.
        self._shutdown_requested = False
        self._local_update_thread = None
        self._private_data = {}  # cloud.my_id_from_remote -> PrivateData mapping
        # self._private_data = collections.MutableMapping()
        self.network_signal = Event()
        # self.network_signal = Semaphore()
        self._io_lock = Lock()
        self.watchdog_worker = WatchdogWorker(self)
        self._nebs_instance = nebs_instance

    def start(self, argv):
        set_mylog_name('nebs')
        # todo process start() args here

        # read in all the .nebs
        db = self.get_db()
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
            target=new_main_thread, args=[self]
            # target = local_update_thread, args = [self]
        )
        self._local_update_thread.start()
        self._local_update_thread.join()

    def spawn_net_thread(self, ipv6_address):
        if self.active_network_obj is not None:
            # todo make sure connections from the old thread get dequeue'd
            self.active_network_obj.shutdown()
        mylog('Spawning new server thread on {}'.format(ipv6_address))
        self.active_network_obj = NetworkThread(ipv6_address, self)

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
            self.filter_func(conn, addr)
            num_conns -= 1
            mylog('processed {} from {}'.format(conn.__class__, addr))

    def is_ipv6(self):
        return self.active_network_obj.is_ipv6()

    def has_private_data(self, cloud):
        return cloud.my_id_from_remote in self._private_data

    def get_private_data(self, cloud):
        # type: (Cloud) -> PrivateData
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
                self._private_data[cloud.my_id_from_remote] = PrivateData(cloud, None)

    def reload_private_data(self, cloud):
        """
        Updates the PrivateData for this cloud. If it already exists, replaces it.
        :param cloud:
        :return:
        """
        # the PrivateData ctor reads existing ones, or creates new ones.
        if cloud.completed_mirroring:
            self._private_data[cloud.my_id_from_remote] = PrivateData(cloud, None)

    def is_private_data_file(self, full_path, cloud=None):
        """
        Returns true if the file at full_path is the .nebs for the given mirror.
        If cloud=None, then it searches all mirrors on this host.
        :param full_path: The FULL path. Not the cloud-relative one.
        :param cloud:
        :return:
        """
        if cloud is None:
            # todo: this is pretty untested. Write some tests that make sure
            db = self.get_db()
            for cloud2 in db.session.query(Cloud).all():
                if cloud2.root_directory == os.path.commonprefix([cloud2.root_directory, full_path]):
                    cloud = cloud2
                    break
        if cloud is None:
            return False
        return os.path.join(cloud.root_directory, '.nebs') == full_path

    def get_client_permissions(self, client_sid, cloud, relative_path):
        db = self.get_db()
        rd = get_client_session(db, client_sid, cloud.uname(), cloud.cname())
        # mylog('get_client_permissions [{}] {}'.format(0, rd))
        if rd.success:
            client = rd.data
            private_data = self.get_private_data(cloud)
            if private_data is not None:
                mylog('Looking up [{}]\'s permission to access <{}>'.format(client.user_id, relative_path))
                return private_data.get_permissions(client.user_id, relative_path)
            else:
                mylog('There has no private data for {}'.format(cloud.name), '31')
        return NO_ACCESS

    def get_db(self):
        return self._nebs_instance.get_db()

    def filter_func(self, connection, address):
        try:
            msg_obj = connection.recv_obj()
        except Exception, e:
            mylog('ERROR: nebs failed to decode a connection from ()'.format(address), '31')
            connection.close()
            return

        mylog('<{}>msg:{}'.format(address, msg_obj.__dict__))
        msg_type = msg_obj.type

        # todo we should make sure the connection was from a host or a client
        # cont   that we were told about here, before doing ANY processing.

        # NOTE: NEVER REMOTE. NEVER ALLOW REMOTE->HOST.
        try:
            # H->H Messages
            if msg_type == HOST_HOST_FETCH:
                handle_fetch(self, connection, address, msg_obj)
            elif msg_type == HOST_FILE_PUSH:
                # This is for HOST_FILE_TRANSFER, REMOVE_FILE. They follow HFP
                handle_file_change(self, connection, address, msg_obj)
            # ----------------------- C->H Messages ----------------------- #
            elif msg_type == STAT_FILE_REQUEST:
                # todo:2 REALLY? This still isnt here? I guess list files does it...
                pass
            elif msg_type == LIST_FILES_REQUEST:
                list_files_handler(self, connection, address, msg_obj)
            elif msg_type == CLIENT_FILE_PUT:
                handle_recv_file_from_client(self, connection, address, msg_obj)
            elif msg_type == READ_FILE_REQUEST:
                handle_read_file_request(self, connection, address, msg_obj)
            elif msg_type == CLIENT_ADD_OWNER:
                handle_client_add_owner(self, connection, address, msg_obj)
            elif msg_type == CLIENT_ADD_CONTRIBUTOR:
                handle_client_add_contributor(self, connection, address, msg_obj)
            elif msg_type == REFRESH_MESSAGE:
                connection.send_obj(RefreshMessageMessage())
                pass  # for now, all we need to do is wake up on this message.
            else:
                mylog('I don\'t know what to do with {},\n{}'.format(msg_obj, msg_obj.__dict__))
        except Exception, e:
            sys.stderr.write(e.message)

        connection.close()

    def client_access_check_or_close(self, connection, client_sid, cloud, rel_path, required_access=READ_ACCESS):
        # type: (AbstractConnection, str, Cloud, str, int) -> ResultAndData
        """

        :param connection:
        :param client_sid:
        :param cloud:
        :param rel_path:
        :param required_access:
        :return:
        """
        permissions = self.get_client_permissions(client_sid, cloud, rel_path)
        rd = ResultAndData(True, permissions)
        if not permissions_are_sufficient(permissions, required_access):
            err = 'Session does not have sufficient permission to access <{}>'.format(rel_path)
            mylog(err, '31')
            response = InvalidPermissionsMessage(err)
            connection.send_obj(response)
            connection.close()
            rd = ResultAndData(False, err)
        bg = '102' if rd.success else '101'
        mylog('c access check {} {} {}'.format(client_sid, rel_path, rd.success), '30;{}'.format(bg))
        return rd

    def acquire_lock(self):
        self._io_lock.acquire()
        # frameinfo = getframeinfo(currentframe().f_back)
        # caller = getframeinfo(currentframe().f_back.f_back)
        # mylog('Locking - {}/{}:{}'.format(
        #     os.path.basename(caller.filename)
        #     , os.path.basename(frameinfo.filename)
        #     , frameinfo.lineno))

    def release_lock(self):
        self._io_lock.release()
        # frameinfo = getframeinfo(currentframe().f_back)
        # caller = getframeinfo(currentframe().f_back.f_back)
        # mylog('Unlocking - {}/{}:{}'.format(
        #     os.path.basename(caller.filename)
        #     , os.path.basename(frameinfo.filename)
        #     , frameinfo.lineno))

    def signal(self):
        self.network_signal.set()
        # frameinfo = getframeinfo(currentframe().f_back)
        # caller = getframeinfo(currentframe().f_back.f_back)
        # mylog('Signaling Host - {}/{}:{}'.format(
        #     os.path.basename(caller.filename)
        #     , os.path.basename(frameinfo.filename)
        #     , frameinfo.lineno))
        # self.network_signal.release()

    def get_instance(self):
        return self._nebs_instance
