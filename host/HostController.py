import atexit
import logging
import os
import signal
import sys
from _socket import gaierror
from threading import Thread, Event, Lock

from common_util import *
from connections.RawConnection import RawConnection
from host.NetworkController import NetworkController
from host.NetworkThread import NetworkThread
from host.PrivateData import PrivateData, NO_ACCESS, READ_ACCESS
from host.WatchdogThread import WatchdogWorker
from host.function.local_updates import new_main_thread
from host.function.network.client import list_files_handler, \
    handle_recv_file_from_client, handle_read_file_request, \
    handle_client_add_owner, handle_client_add_contributor
from host.function.network_updates import handle_fetch, handle_file_change
from host.models.Cloud import Cloud
from host.util import set_mylog_name, mylog, get_ipv6_list, setup_remote_socket, \
    get_client_session, permissions_are_sufficient
from messages.RefreshMessageMessage import RefreshMessageMessage
from messages import InvalidPermissionsMessage

from msg_codes import HOST_HOST_FETCH, HOST_FILE_PUSH, \
    STAT_FILE_REQUEST, LIST_FILES_REQUEST, CLIENT_FILE_PUT, READ_FILE_REQUEST, \
    CLIENT_ADD_OWNER, CLIENT_ADD_CONTRIBUTOR, REFRESH_MESSAGE

__author__ = 'Mike'


class HostController:
    def __init__(self, nebs_instance):
        # type: (NebsInstance) -> HostController
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
        self._network_controller = None

    def start(self, argv):
        # type: ([str]) -> None
        _log = get_mylog()
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

        # register the shutdown callback
        atexit.register(self.shutdown)

        force_kill = '--force' in argv
        if force_kill:
            _log.info('Forcing shutdown of previous instance')
        rd = self._nebs_instance.start(force_kill)

        if rd.success:
            try:
                self._network_controller = NetworkController(self)
            except Exception, e:
                _log.error('Failed to instantiate NetworkController')
                mylog(e.message, '31')
                self.shutdown()
                sys.exit(-1)

        if rd.success:
            rd = self._network_controller.refresh_external_ip()
            if rd.success:
                connected = rd.data
                if connected:
                    self.spawn_net_thread()
            else:
                err_msg = rd.data
                _log.error(err_msg)
            # ipv6_addresses = get_ipv6_list()
            # if len(ipv6_addresses) < 1:
            #     mylog('Couldn\'t acquire an IPv6 address')
            # else:
            #     self.spawn_net_thread(ipv6_addresses[0])
            #     # local_update thread will handle the first handshake/host setup

            try:
                self.do_local_updates()
            finally:
                self.shutdown()

            _log.info('Both the local update checking thread and the network thread'
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

    def spawn_net_thread(self):
        # _log = logging.getLogger(__name__)
        _log = get_mylog()
        if self.active_network_obj is not None:
            # todo make sure connections from the old thread get dequeue'd
            self.active_network_obj.shutdown()
            self._do_network_shutdown()

        # mylog('Spawning new server thread on {}'.format(ipv6_address))
        external_ip, internal_ip = self._network_controller.get_external_ip(), self._network_controller.get_local_ip()
        _log.info('Spawning new server thread on mapping [{}->{}]'.format(external_ip, internal_ip))
        self.active_network_obj = NetworkThread(external_ip, internal_ip, self)

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


    def check_ipv6_changed(self, curr_ipv6):
        ipv6_addresses = get_ipv6_list()
        if curr_ipv6 is None:
            if len(ipv6_addresses) > 0:
                return True, ipv6_addresses[0]
            else:
                return False, None
        if curr_ipv6 in ipv6_addresses:
            return False, None
        else:
            new_addr = None
            if len(ipv6_addresses) > 1:
                new_addr = ipv6_addresses[0]
            return True, new_addr

    def update_network_status(self):
        # New
        rd = self._network_controller.refresh_external_ip()
        if rd.success:
            changed = rd.data
            if changed:
                rd = self.change_ip()
        if rd.success:
            # handshake remotes will send all of them our new IP/port/wsport
            rd = self.handshake_remotes()
        # If these fail, we probably don't have a network anymore.
        # If they're fatal, they'll have thrown an exception (hopefully)

        return rd


    # def check_network_change(self):
    #     """
    #     Checks to see if the state of the network has changed.
    #     If it has, it tries to reconnect to the remote using the new information.
    #     """
    #     # OLD
    #     rd = Success()
    #     mirrored_clouds = db.session.query(Cloud).filter_by(completed_mirroring=True)
    #     all_mirrored_clouds = mirrored_clouds.all()
    #     # check if out ip has changed since last update
    #     ip_changed, new_ip = False, None
    #     if self.is_ipv6():
    #         ip_changed, new_ip = check_ipv6_changed(self.active_ipv6())
    #     # mylog('Done checking IP change')
    #     # if the ip is different, move our server over
    #     if ip_changed:
    #         rd = self.change_ip(new_ip, all_mirrored_clouds)
    #         # todo: what if one of the remotes fails to handshake?
    #         # should store the last handshake per remote
    #         # if rd.success:
    #         #     last_handshake = datetime.utcnow()
    #         #     current_ipv6 = new_ip
    #
    #     return rd

    def is_shutdown_requested(self):
        return self._shutdown_requested

    def shutdown(self):
        mylog('Calling HostController.shutdown()')
        self._shutdown_requested = True
        self._do_network_shutdown()

        if self._local_update_thread is not None:
            try:
                self._local_update_thread.join()
            except RuntimeError, e:
                pass

        if self._nebs_instance is not None:
            self._nebs_instance.shutdown()

    def _do_network_shutdown(self):
        if self.active_network_obj is not None:
            self.active_network_obj.shutdown()
        # TODO make sure to kill these threads too.
        if self.active_network_thread is not None:
            pass
        if self.active_ws_thread is not None:
            pass

    def change_ip(self):
        if self.active_network_obj is not None:
            self.active_network_obj.shutdown()
        self.spawn_net_thread()
        return Success()

    # def change_ip(self, new_ip, clouds):
    #     if new_ip is None:
    #         if self.active_ipv6() is not None:
    #             mylog('I should tell all the remotes that I\'m dead now.')  # fixme
    #             mylog('DISCONNECTED FROM IPv6')  # fixme
    #         # at this point, how is my active net thread connected to anything?
    #         if self.active_network_obj is not None:
    #             self.active_network_obj.shutdown()
    #     else:
    #         self.spawn_net_thread(new_ip)
    #         for cloud in clouds:
    #             self.send_remote_handshake(cloud)
    #     return Success()

    # def handshake_clouds(self, clouds):
    #     mylog('Telling {}\'s remote that {}\'s at {}'.format(
    #         [cloud.name for cloud in clouds]
    #         , [cloud.my_id_from_remote for cloud in clouds]
    #         , self.active_ipv6())
    #     )
    #     for cloud in clouds:
    #         self.send_remote_handshake(cloud)

    def handshake_remotes(self):
        db = self._nebs_instance.get_db()

        mirrored_clouds = db.session.query(Cloud).filter_by(completed_mirroring=True)
        all_mirrored_clouds = mirrored_clouds.all()
        # todo: In the future, have one Remote object in the host DB for each remote
        # and handshake that remote once.
        # todo: And then update that Remote's handshake
        for cloud in all_mirrored_clouds:
            self.send_remote_handshake(cloud)
        # map(self.send_remote_handshake, all_mirrored_clouds)
        return Success()

    def send_remote_handshake(self, cloud):
        # mylog('Telling {}\'s remote that [{}]\'s at {}'.format(
        #     cloud.name, cloud.my_id_from_remote, self.active_ipv6())
        # )
        remote_conn = None
        try:
            remote_sock = setup_remote_socket(cloud.remote_host, cloud.remote_port)
            remote_conn = RawConnection(remote_sock)
            msg = cloud.generate_handshake(
                self.active_network_obj.get_external_ip()
                , self.active_network_obj.get_external_port()
                , self.active_network_obj.get_external_ws_port()
            )

            remote_conn.send_obj(msg)
            # todo
            # response = remote_conn.recv_obj()
        except gaierror, e:
            mylog('Failed to connect to remote')
            mylog('likely a network failure.')
            mylog('Even more likely, network disconnected.')
            mylog(e.message)
            self.shutdown()
            mylog('I\'m shutting it down, because I don\'t know how to recover quite yet.')
        except Exception, e:
            mylog('some other error handshaking remote')
            mylog(e.message)
            self.shutdown()
            mylog('I\'m shutting it down, because I don\'t know how to recover quite yet.')
        finally:
            if remote_conn is not None:
                remote_conn.close()

    def process_connections(self):
        num_conns = len(self.active_network_obj.connection_queue)
        while num_conns > 0:
            (conn, addr) = self.active_network_obj.connection_queue.pop(0)
            # for (conn, addr) in self.active_network_obj.connection_queue[:]:
            try:
                self.filter_func(conn, addr)
            except Exception, e:
                mylog('Error handling connection')
                mylog(e.message)
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

    def get_net_controller(self):
        return self._network_controller
