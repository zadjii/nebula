import atexit
import logging
import logging.handlers
import os
import signal
import sys
from inspect import getframeinfo, currentframe

from OpenSSL import crypto
from _socket import gaierror
from threading import Thread, Event, Lock

from twisted.internet import reactor

from common_util import *
from connections.AbstractConnection import AbstractConnection
from connections.AlphaEncryptionConnection import AlphaEncryptionConnection
from connections.RawConnection import RawConnection
from host.NebsInstance import NebsInstance
from host.NetworkController import NetworkController
from host.NetworkThread import NetworkThread
from host.PrivateData import PrivateData, NO_ACCESS, READ_ACCESS
from host.WatchdogThread import WatchdogWorker
from host.function.network.client import list_files_handler, \
    handle_recv_file_from_client, handle_read_file_request, \
    handle_client_add_owner, handle_client_add_contributor, handle_client_make_directory, handle_client_get_permissions, \
    handle_client_get_shared_paths, handle_client_create_link, handle_client_read_link, stat_files_handler, \
    handle_client_delete_file, handle_client_remove_dir, handle_client_set_link_permissions, \
    handle_client_add_user_to_link, handle_client_remove_user_from_link, handle_client_get_link_permissions
from host.function.network_updates import handle_fetch, handle_file_sync_request
from host.models.Cloud import Cloud
from host.models.Remote import Remote
from host.util import set_mylog_name, mylog, get_ipv6_list, setup_remote_socket, \
    get_client_session, permissions_are_sufficient, create_key_pair, create_cert_request
from messages import *

from msg_codes import *

__author__ = 'Mike'


class HostController:
    def __init__(self, nebs_instance):
        # type: (NebsInstance) -> None
        self.active_net_thread_obj = None
        self.active_network_thread = None
        self.active_ws_thread = None
        self.network_queue = []  # all the queued connections to handle.
        self._shutdown_requested = False
        self._local_update_thread = None
        self._private_data = {}  # cloud.my_id_from_remote -> PrivateData mapping
        self.network_signal = Event()
        self._io_lock = Lock()
        self.watchdog_worker = WatchdogWorker(self)
        self._nebs_instance = nebs_instance
        self._network_controller = None
        # if we've failed to send to the network, then set _is_online to false.
        #   Next time we've handshaken the remotes, we'll set this back to true.
        self._is_online = True
        self._client_log = get_mylog()

    def start(self, force_kill=False, access_log=None):
        # type: (bool, str) -> None
        _log = get_mylog()
        set_mylog_name('nebs')

        if access_log is not None:
            msg = 'writing access log to {}'.format(access_log)
            _log.debug(msg)
            print(msg)
            self.create_client_logger(access_log)

        # read in all the .nebs
        db = self.get_db()
        for cloud in db.session.query(Cloud).all():
            self.load_private_data(cloud)
        # db.session.close()
        # if the mirror was completed before we started, great. We add their
        # .nebs at launch, no problem.
        # what if we complete mirroring while we're running?
        #   regardless if it has a .nebs (existing) or not (new/1st mirror)

        # register the shutdown callback
        atexit.register(self.shutdown)

        if force_kill:
            _log.info('Forcing shutdown of previous instance')
        rd = self._nebs_instance.start(force_kill)

        if rd.success:
            try:
                self._network_controller = NetworkController(self.get_instance())
            except Exception, e:
                _log.error('Failed to instantiate NetworkController')
                mylog(e.message, '31')
                self.shutdown()
                sys.exit(-1)

        if rd.success:
            self.update_network_status()
            try:
                self.do_local_updates()
            finally:
                self.shutdown()

            _log.info('Both the local update checking thread and the network thread'
                      ' have exited.')
            sys.exit()
        return rd

    def do_local_updates(self):
        _log = get_mylog()
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        from host.function.local_updates import new_main_thread

        self._local_update_thread = Thread(
            target=new_main_thread, args=[self]
        )
        self._local_update_thread.start()
        _log.debug('Before reactor.run')
        reactor.run(installSignalHandlers=0)
        _log.debug('After reactor.run')
        self._local_update_thread.join()

    def spawn_net_thread(self):
        _log = get_mylog()
        if self.active_net_thread_obj is not None:
            # todo make sure connections from the old thread get dequeue'd
            self.active_net_thread_obj.shutdown()
            self._do_network_shutdown()

        # mylog('Spawning new server thread on {}'.format(ipv6_address))
        external_ip, internal_ip = self._network_controller.get_external_ip(), self._network_controller.get_local_ip()
        _log.info('Spawning new server thread on mapping [{}->{}]'.format(external_ip, internal_ip))
        self.active_net_thread_obj = NetworkThread(external_ip, internal_ip, self)

        self.active_network_thread = Thread(
            target=self.active_net_thread_obj.work_thread, args=[]
        )
        self.active_network_thread.start()

        self.active_ws_thread = Thread(
            target=self.active_net_thread_obj.ws_work_thread, args=[]
        )
        self.active_ws_thread.start()

    def active_ipv6(self):
        if self.active_net_thread_obj is not None:
            return self.active_net_thread_obj.ipv6_address
        else:
            return None

    @staticmethod
    def check_ipv6_changed(curr_ipv6):
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
        """
        Check the status of the network. If the network controller indicates
          that the network status has changed (our IP is different now), then
          we're going to send a handshake to each of the remotes.
        Called by:
        `new_main_thread`, near the top of the loop, before checking for local
          updates.
        :return:
        """
        db = self._nebs_instance.get_db()
        _log = get_mylog()
        # New
        rd = self._network_controller.refresh_external_ip()
        if rd.success:
            changed = rd.data
            if changed:
                rd = self.change_ip()
                if rd.success:
                    # TODO: Right now I'm just kinda ignoring the RD's here...

                    # # handshake remotes will send all of them our new IP/port/wsport
                    # rd = self.handshake_remotes()

                    # Part 2:
                    # Handshake each remote once for this host.
                    self.refresh_remotes()
                    if rd.success:
                        rd = Success(changed)
        else:
            err_msg = rd.data
            _log.error(err_msg)
        return rd

        # If these fail, we probably don't have a network anymore.
        # If they're fatal, they'll have thrown an exception (hopefully)

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
        if self.active_net_thread_obj is not None:
            self.active_net_thread_obj.shutdown()
        # TODO make sure to kill these threads too.
        if self.active_network_thread is not None:
            pass
        if self.active_ws_thread is not None:
            pass

    def change_ip(self):
        if self.active_net_thread_obj is not None:
            self.active_net_thread_obj.shutdown()
        self.spawn_net_thread()
        return Success()

    # We're removing this. HostMove is responsible for updating the Remote with
    # this host's address. MirrorHandshake is now responsible for updating
    # timestanps.
    # def handshake_remotes(self):
    #     """
    #     Sends HostHandshakeMessages to the remote for each mirror on this host.
    #     Called by:
    #     `HostController::update_network_status`, if our IP changed we handshake all remotes.
    #     `new_new_main_thread`, if the number of mirrors has changed
    #     `new_new_main_thread`, if it's been 30s since the last handshake
    #     :return:
    #     """
    #     db = self._nebs_instance.get_db()
    #     # Part 1: Legacy
    #     # Handshake the remote for each mirror on this host.
    #     # This does not update our cert, or really our IP.
    #     # todo#63: In the future, have one Remote object in the host DB for each remote
    #     #   and handshake that remote once.
    #     # todo: And then update that Remote's handshake (#63?)
    #     mirrors = db.session.query(Cloud).filter_by(completed_mirroring=True)
    #     all_mirrors = mirrors.all()
    #     for mirror in all_mirrors:
    #         self.send_remote_handshake(mirror)
    #     return Success()

    def refresh_remotes(self):
        """
        Sends HostMove messages to each remote we have.
        Also forces the ssl context(s) to refresh with the new certs we receive, if any.
        :return:
        """
        db = self._nebs_instance.get_db()
        all_remotes = db.session.query(Remote).all()
        for remote in all_remotes:
            # todo#62: Check the return value here.
            # TODO#62: If we fail to handshake even one remote, we set ourselves to offlne mode.
            #   If the next remote we DO connect to successfully, we'll be set back into online mode.
            #   This could be due to one remote being offline but another being online.
            #   Our online state should probably be an OR of each remote's individual online states.
            self.send_host_move(remote)
            # todo#64: Hey, now there's handshake_remotes and refresh_remotes.
            #   These do different things, but _really_ they do the same thing.
            #   Maybe we should do something about that.. like consolidate them.
            # NOTE 2019-02-21: Maybe not. cert handshaking is a different thing
            #   than mirror handshaking. Don't consolidate them.

        self.active_net_thread_obj.refresh_context()

        return Success()

    def try_mirror_handshake(self, cloud):
        # type: (Cloud) -> ResultAndData
        # type: (Cloud) -> ResultAndData(true, RawConnection)
        remote_conn = None
        _log = get_mylog()

        try:
            rd = setup_remote_socket(cloud)
            if not rd.success:
                return rd
            remote_sock = rd.data
            remote_conn = RawConnection(remote_sock)
            msg = cloud.generate_mirror_handshake()
            _log.debug('sending MirrorHandshake({})'.format(msg.serialize()))
            remote_conn.send_obj(msg)

        except gaierror as e:
            _log.error('Failed to connect to remote for a MirrorHandshake')
            _log.debug('likely a network failure.')
            _log.debug('Even more likely, network disconnected.')
            _log.error(e.message)
            return Error(e.message)
        except Exception, e:
            _log.error('Some other error handshaking remote')
            _log.error(e.message)
            return Error(e.message)
        # finally:
        #     if remote_conn is not None:
        #         remote_conn.close()
        return Success(remote_conn)

    # def send_remote_handshake(self, cloud):
    #     # type: (Cloud) -> ResultAndData
    #     """
    #     Sends a single HostHandshake message to a remote for the given Mirror on this host.
    #     Called by `handshake_remotes`
    #     :param cloud:
    #     :return:
    #     """
    #     _log = get_mylog()
    #     # mylog('Telling {}\'s remote that [{}]\'s at {}'.format(
    #     #     cloud.name, cloud.my_id_from_remote, self.active_ipv6())
    #     # )
    #     attempts = 0
    #     succeeded = False
    #     rd = Error()
    #     while attempts < 5:
    #         rd = self._try_mirror_handshake(cloud)
    #         succeeded = rd.success
    #         if succeeded:
    #             break
    #         attempts += 1
    #         _log.debug('Attempted to handshake cloud, error was "{}"'.format(rd.data))

    #     if not succeeded:
    #         _log.debug('Failed to handshake the remote. Moving to offline mode.')
    #         self.set_offline()
    #     else:
    #         self.set_online()
    #     return rd

    def _try_move(self, remote, message, ip, new_key):
        # type: (Remote, HostMoveRequestMessage, str, crypto.PKey) -> ResultAndData
        _log = get_mylog()
        db = self._nebs_instance.get_db()
        rd = remote.setup_socket()
        if rd.success:
            ssl_socket = rd.data
            raw_conn = RawConnection(ssl_socket)
            _log.info('Host [{}] is moving to new address "{}"'.format(remote.my_id_from_remote, ip))
            raw_conn.send_obj(message)
            resp_obj = raw_conn.recv_obj()
            if resp_obj.type == HOST_MOVE_RESPONSE:
                remote.set_certificate(ip, resp_obj.crt)
                remote.my_id_from_remote = resp_obj.host_id
                remote.key = crypto.dump_privatekey(crypto.FILETYPE_PEM, new_key)
                db.session.add(remote)
                rd = Success(remote)
            else:
                msg = 'Failed to move the host on the remote - got bad response.'
                _log.error(msg)
                _log.error('response was "{}"'.format(resp_obj.serialize()))
                rd = Error(msg)
        else:
            msg = 'Failed to connect to the remote for moving to a new address'
            _log.error(msg)
        return rd

    def send_host_move(self, remote):
        # type: (Remote) -> ResultAndData
        _log = get_mylog()
        db = self._nebs_instance.get_db()

        new_key = create_key_pair(crypto.TYPE_RSA, 2048)
        ip = self._network_controller.get_external_ip()
        port = self.active_net_thread_obj.get_external_port()
        ws_port = self.active_net_thread_obj.get_external_ws_port()

        hostname = platform.uname()[1]
        req = create_cert_request(new_key, CN=ip)
        certificate_request_string = crypto.dump_certificate_request(crypto.FILETYPE_PEM, req)
        message = HostMoveRequestMessage(remote.my_id_from_remote, ip, certificate_request_string, port, ws_port, hostname)

        attempts = 0
        succeeded = False
        rd = Error()
        while attempts < 5:
            rd = self._try_move(remote, message, ip, new_key)
            if rd.success:
                succeeded = True
                break
            attempts += 1

        if not succeeded:
            _log.debug('Failed to host_move the remote. Moving to offline mode.')
            self.set_offline()
        else:
            self.set_online()
        return rd

    def process_connections(self):
        num_conns = len(self.active_net_thread_obj.connection_queue)
        while num_conns > 0:
            (conn, addr) = self.active_net_thread_obj.connection_queue.pop(0)
            # for (conn, addr) in self.active_network_obj.connection_queue[:]:
            try:
                self.filter_func(conn, addr)
            except Exception as e:
                mylog('Error handling connection')
                mylog(e.message)
            num_conns -= 1
            mylog('processed {} from {}'.format(conn.__class__, addr))

    def is_ipv6(self):
        return self.active_net_thread_obj.is_ipv6()

    def has_private_data(self, cloud):
        return cloud.my_id_from_remote in self._private_data

    def get_private_data(self, cloud):
        # type: (Cloud) -> PrivateData
        if self.has_private_data(cloud):
            return self._private_data[cloud.my_id_from_remote]
        return None

    def find_link_clouds(self, link_id):
        # type: (str) -> [Cloud]
        db = self.get_db()
        matches = []
        for data in self._private_data.values():
            matches.append(db.session.query(Cloud).get(data._cloud_id))
        return matches

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
        # type: (str, Cloud, RelativePath) -> int
        db = self.get_db()

        rd = get_client_session(db, client_sid, cloud.uname(), cloud.cname())
        if rd.success:
            client = rd.data
            private_data = self.get_private_data(cloud)
            if private_data is not None:
                is_public = client is None
                if is_public:
                    mylog('Looking up [PUBLIC]\'s permission to access <{}>'.format(relative_path.to_string()))
                    return private_data.get_permissions(PUBLIC_USER_ID, relative_path)
                else:
                    mylog('Looking up [{}]\'s permission to access <{}>'.format(client.user_id, relative_path.to_string()))
                    return private_data.get_permissions(client.user_id, relative_path)
            else:
                mylog('There is no private data for {}'.format(cloud.name), '31')
        return NO_ACCESS

    def get_link_permissions(self, client_sid, cloud, link_str):
        # type: (str, Cloud, str) -> int
        db = self.get_db()

        rd = get_client_session(db, client_sid, cloud.uname(), cloud.cname())
        if rd.success:
            client = rd.data
            private_data = self.get_private_data(cloud)
            if private_data is not None:
                is_public = client is None
                if is_public:
                    mylog('Looking up [PUBLIC]\'s permission to access <{}>'.format(link_str))
                    return private_data.get_link_permissions(PUBLIC_USER_ID, link_str)
                else:
                    mylog('Looking up [{}]\'s permission to access <{}>'.format(client.user_id, link_str))
                    return private_data.get_link_permissions(PUBLIC_USER_ID, link_str)
            else:
                mylog('There is no private data for {}'.format(cloud.name), '31')
        return NO_ACCESS

    def get_db(self):
        # return self._nebs_instance.make_db_session()
        return self._nebs_instance.get_db()

    def filter_func(self, connection, address):
        try:
            msg_obj = connection.recv_obj()
        except Exception as e:
            mylog('ERROR: nebs failed to decode a connection from ({})'.format(address), '31')
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
            # HostFilePush is being removed in favor of FileChangeProposal
            # elif msg_type == HOST_FILE_PUSH:
            #     # This is for HOST_FILE_TRANSFER, REMOVE_FILE. They follow HFP
            #     handle_file_change(self, connection, address, msg_obj)
            elif msg_type == REFRESH_MESSAGE:
                connection.send_obj(RefreshMessageMessage())
            # Note: FILE_SYNC_PROPOSAL's are only sent as a response to a
            # FILE_SYNC_REQUEST. The FSR handler will handle the proposal directly.
            # elif msg_type == FILE_SYNC_PROPOSAL:
            #     handle_file_change_proposal(self, connection, address, msg_obj)
            elif msg_type == FILE_SYNC_REQUEST:
                handle_file_sync_request(self, connection, address, msg_obj)
            # ------------------------ C->H Messages ------------------------ #
            elif msg_type == STAT_FILE_REQUEST:
                stat_files_handler(self, connection, address, msg_obj)
            elif msg_type == LIST_FILES_REQUEST:
                list_files_handler(self, connection, address, msg_obj)
            # elif msg_type == CLIENT_FILE_PUT:
            #     mylog('Received a CLIENT_FILE_PUT. We\'re deprecating that message, use CLIENT_FILE_TRANSFER instead')
            elif msg_type == CLIENT_FILE_TRANSFER:
                handle_recv_file_from_client(self, connection, address, msg_obj)
            elif msg_type == READ_FILE_REQUEST:
                handle_read_file_request(self, connection, address, msg_obj)
            elif msg_type == CLIENT_ADD_OWNER:
                handle_client_add_owner(self, connection, address, msg_obj)
            elif msg_type == CLIENT_ADD_CONTRIBUTOR:
                handle_client_add_contributor(self, connection, address, msg_obj)
            elif msg_type == CLIENT_UPGRADE_CONNECTION_REQUEST:
                self.handle_connection_upgrade(connection, address, msg_obj)
            elif msg_type == CLIENT_MAKE_DIRECTORY:
                handle_client_make_directory(self, connection, address, msg_obj)
            elif msg_type == CLIENT_GET_PERMISSIONS:
                handle_client_get_permissions(self, connection, address, msg_obj)
            elif msg_type == CLIENT_GET_SHARED_PATHS:
                handle_client_get_shared_paths(self, connection, address, msg_obj)
            elif msg_type == CLIENT_CREATE_LINK_REQUEST:
                handle_client_create_link(self, connection, address, msg_obj)
            elif msg_type == CLIENT_READ_LINK:
                handle_client_read_link(self, connection, address, msg_obj)
            elif msg_type == CLIENT_DELETE_FILE_REQUEST:
                handle_client_delete_file(self, connection, address, msg_obj)
            elif msg_type == CLIENT_DELETE_DIR_REQUEST:
                handle_client_remove_dir(self, connection, address, msg_obj)
            elif msg_type == CLIENT_SET_LINK_PERMISSIONS:
                handle_client_set_link_permissions(self, connection, address, msg_obj)
            elif msg_type == CLIENT_ADD_USER_TO_LINK:
                handle_client_add_user_to_link(self, connection, address, msg_obj)
            elif msg_type == CLIENT_REMOVE_USER_FROM_LINK:
                handle_client_remove_user_from_link(self, connection, address, msg_obj)
            elif msg_type == CLIENT_GET_LINK_PERMISSIONS_REQUEST:
                handle_client_get_link_permissions(self, connection, address, msg_obj)
            else:
                mylog('I don\'t know what to do with {},\n{}'.format(msg_obj, msg_obj.__dict__))
        except Exception as e:
            sys.stderr.write(e.message)

        connection.close()

    def handle_connection_upgrade(self, connection, address, msg_obj):
        # type: (AbstractConnection, str, ClientUpgradeConnectionRequestMessage) -> ResultAndData
        """
        Process a ClientUpgradeConnectionRequestMessage. These are messages that
            cause a change in how data is processed from the connection. Another
            message will be handled with the upgraded connection.
        :param connection:
        :param address:
        :param msg_obj:
        :return:
        """
        _log = get_mylog()

        msg_type = msg_obj.type
        if msg_type != CLIENT_UPGRADE_CONNECTION_REQUEST:
            return Error('handle_connection_upgrade without CLIENT_UPGRADE_CONNECTION_REQUEST')

        upgrade_type = msg_obj.upgrade_type
        value = msg_obj.value
        if upgrade_type == ENABLE_ALPHA_ENCRYPTION:
            rd = self.do_alpha_encryption_upgrade(connection, value)
        else:
            rd = Error('Unknown upgrade type {}'.format(upgrade_type))

        if rd.success:
            _log.debug('Connection successfully upgraded')
            new_conn = rd.data
            self.filter_func(new_conn, address)

    def do_alpha_encryption_upgrade(self, connection, client_public_key_hex_string):
        # type: (AbstractConnection, str) -> ResultAndData
        _log = get_mylog()
        _log.debug('initiating alpha encryption upgrade')
        upgraded_connection = AlphaEncryptionConnection(connection, client_public_key_hex_string)
        upgraded_connection.send_setup_response()
        _log.debug('sent upgrade response')

        return Success(upgraded_connection)

    def client_access_check_or_close(self, connection, client_sid, cloud, rel_path, required_access=READ_ACCESS):
        # type: (AbstractConnection, str, Cloud, RelativePath, int) -> ResultAndData
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
            err = 'Session does not have sufficient permission to access <{}>'.format(rel_path.to_string())
            mylog(err, '31')
            response = InvalidPermissionsMessage(err)
            connection.send_obj(response)
            connection.close()
            rd = ResultAndData(False, err)
        bg = '102' if rd.success else '101'
        mylog('c access check {} {} {}'.format(client_sid, rel_path, rd.success), '30;{}'.format(bg))
        return rd

    def client_link_access_check_or_close(self, connection, client_sid, cloud, link_str, required_access=READ_ACCESS):
        # type: (AbstractConnection, str, Cloud, str, int) -> ResultAndData
        """

        :param connection:
        :param client_sid:
        :param cloud:
        :param rel_path:
        :param required_access:
        :return:
        """
        permissions = self.get_link_permissions(client_sid, cloud, link_str)
        rd = ResultAndData(True, permissions)
        if not permissions_are_sufficient(permissions, required_access):
            err = 'Session does not have sufficient permission to access <{}>'.format(link_str)
            mylog(err, '31')
            response = InvalidPermissionsMessage(err)
            connection.send_obj(response)
            connection.close()
            rd = ResultAndData(False, err)
        bg = '102' if rd.success else '101'
        mylog('c access check {} {} {}'.format(client_sid, link_str, rd.success), '30;{}'.format(bg))
        return rd

    def acquire_lock(self):
        self._io_lock.acquire()
        frameinfo = getframeinfo(currentframe().f_back)
        caller = getframeinfo(currentframe().f_back.f_back)
        get_mylog().debug('Locking Host - {}/{}:{}'.format(os.path.basename(caller.filename),
                                                           os.path.basename(frameinfo.filename),
                                                           frameinfo.lineno))

    def release_lock(self):
        frameinfo = getframeinfo(currentframe().f_back)
        caller = getframeinfo(currentframe().f_back.f_back)
        get_mylog().debug('Unlocking Host - {}/{}:{}'.format(os.path.basename(caller.filename),
                                                             os.path.basename(frameinfo.filename),
                                                             frameinfo.lineno))
        self._io_lock.release()

    def signal(self):
        frameinfo = getframeinfo(currentframe().f_back)
        caller = getframeinfo(currentframe().f_back.f_back)
        get_mylog().debug('Signaling Host - {}/{}:{}'.format(os.path.basename(caller.filename),
                                                             os.path.basename(frameinfo.filename),
                                                             frameinfo.lineno))
        self.network_signal.set()

    def get_instance(self):
        # type: () -> NebsInstance
        return self._nebs_instance

    def get_net_controller(self):
        # type: () -> NetworkController
        return self._network_controller

    def is_online(self):
        # type: () -> bool
        """
        Returns true if the host is currently online and capable of sending
        updates to the network.
        :return:
        """
        return self._is_online

    def set_offline(self):
        self._is_online = False

    def set_online(self):
        self._is_online = True

    def log_client(self, client, verb, cloud, relative_path, result):
        msg = '[{}] {} {}:{}=>{}'.format(
            client.user_id if client else 'PUBLIC'
            , verb
            , cloud.full_name()
            , relative_path.to_string() if relative_path else '#'
            , result
        )
        self._client_log.info(msg)

    def log_client_sid(self, client_sid, verb, cloud, relative_path, result):
        rd = get_client_session(self.get_db(), client_sid, cloud.uname(), cloud.cname())
        if rd.success:
            client = rd.data
        else:
            client = None
        self.log_client(client, verb, cloud, relative_path, result)

    def create_client_logger(self, filename=None, level=logging.INFO):
        _log = getLogger('client')
        for h in _log.handlers:
            _log.removeHandler(h)
        if filename is None:
            hdlr = logging.StreamHandler()
        else:
            # todo: make this a configurable number of bytes
            hdlr = logging.handlers.RotatingFileHandler(
                    filename, maxBytes=100*1024*1024, backupCount=5)
        _log.setLevel(level)
        formatter = logging.Formatter('%(asctime)s|(%(levelname)s) %(message)s')
        hdlr.setFormatter(formatter)
        _log.addHandler(hdlr)
        _log.propagate = False
        self._client_log = _log

    def _find_mirror_for_file(self, full_path):
        # type: (str) -> Cloud
        # type: (str) -> Optional[Cloud]
        db = self.get_db()
        all_clouds = db.session.query(Cloud).all()
        for c in all_clouds:
            norm_root = os.path.normpath(c.root_directory + os.sep)
            norm_path = os.path.normpath(full_path)
            if norm_path.startswith(norm_root):
                return c
        return None

    def local_create_file(self, full_path, timestamp=None):
        # type: (str, datetime) -> ResultAndData
        _log = get_mylog()
        cloud = self._find_mirror_for_file(full_path)
        if cloud is None:
            # we noticed a file creation for a path that isn't under an existing
            #   cloud. We should just ignore this.
            return Error()
        db = self.get_db()
        rd = cloud.create_file(full_path, db=db, timestamp=timestamp)
        if rd.success:
            db.session.commit()
            # db.session.close()
            # db = None
        else:
            _log.error('Encountered an error while creating the file <{}> (HostController::local_create_file)'.format(full_path))
            _log.error(rd.data)
            # todo rollback? error?
            pass
        return rd

    def local_modify_file(self, full_path, timestamp=None):
        # type: (str, datetime) -> ResultAndData
        _log = get_mylog()
        cloud = self._find_mirror_for_file(full_path)
        if cloud is None:
            # we noticed a file creation for a path that isn't under an existing
            #   cloud. We should just ignore this.
            return Error()
        db = self.get_db()
        rd = cloud.modify_file(full_path, db=db, timestamp=timestamp)
        if rd.success:
            db.session.commit()
            # db.session.close()
            # db = None
        else:
            _log.error('Encountered an error while modifying the file <{}> (HostController::local_modify_file)'.format(full_path))
            _log.error(rd.data)
            # todo rollback? error?
            pass
        return rd

    def local_delete_file(self, full_path, timestamp=None):
        # type: (str, datetime) -> ResultAndData
        _log = get_mylog()
        cloud = self._find_mirror_for_file(full_path)
        if cloud is None:
            # we noticed a file creation for a path that isn't under an existing
            #   cloud. We should just ignore this.
            return Error()
        db = self.get_db()
        rd = cloud.delete_file(full_path, db=db, timestamp=timestamp)
        if rd.success:
            db.session.commit()
            # db.session.close()
            # db = None
        else:
            _log.error('Encountered an error while deleting the file <{}> (HostController::local_delete_file)'.format(full_path))
            _log.error(rd.data)
            # todo rollback? error?
            pass
        return rd

    def local_move_file(self, src_path, target_path):
        # type: (str, str) -> ResultAndData
        _log = get_mylog()
        src_cloud = self._find_mirror_for_file(src_path)
        if src_cloud is None:
            # we noticed a file creation for a path that isn't under an existing
            #   cloud. We should just ignore this.
            return Error()
        tgt_cloud = self._find_mirror_for_file(target_path)
        if tgt_cloud is None:
            # we noticed a file creation for a path that isn't under an existing
            #   cloud. We should just ignore this.
            return Error()
        if src_cloud.id is not tgt_cloud.id:
            # TODO: this does seem like an error we should maybe do something with
            return Error()
        db = self.get_db()
        rd = src_cloud.move_file(src_path, target_path, db=db)
        if rd.success:
            db.session.commit()
            # db.session.close()
            # db = None
        else:
            # todo rollback? error?
            _log.error('Encountered an error while moving the file <{}> (HostController::local_move_file)'.format(src_path))
            _log.error(rd.data)
            pass
        return rd
