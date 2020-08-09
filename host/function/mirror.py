import argparse
import os
from datetime import datetime
import socket
import getpass
from sys import stdin
import platform
from time import sleep

from OpenSSL import crypto

from common.BaseCommand import BaseCommand
from common.SimpleDB import SimpleDB
from common_util import *
from connections.AbstractConnection import AbstractConnection
from connections.RawConnection import RawConnection

from host import Cloud, REMOTE_PORT
from host.NebsInstance import NebsInstance
from host.NetworkController import NetworkController
from host.PrivateData import PrivateData
from host.function.recv_files import recv_file_tree
from host.models.Remote import Remote
from host.util import check_response, setup_remote_socket, mylog, get_ipv6_list, lookup_remote, create_key_pair, \
    create_cert_request, setup_ssl_socket_for_address
from messages import *
from msg_codes import *

__author__ = 'Mike'

# FIXME TODO
# Hey there. So I'm looking at this code.
# It looks not super great.
# seems to me like there should be no way to create a Host without also mirroring,
# because this is stupid so yea definitely combine them into one message


# def ask_remote_for_id(instance, host, port, db):
#     """This performs a code [0] message on the remote host at host:port.
#      Awaits a code[1] from the remote.
#      Creates a new Cloud for this host:port.
#      Returns a (0,cloud.id) if it successfully gets something back.
#      """
#     sslSocket = setup_remote_socket(host, port)
#     raw_conn = RawConnection(sslSocket)
#     # write_msg(make_new_host_json(HOST_PORT), sslSocket)
#     ipv6_addresses = get_ipv6_list()
#     if len(ipv6_addresses) < 1:
#         mylog('MY IPV6\'s ARE {}'.format(ipv6_addresses), '31')
#         mylog('ERR: could not find an ipv6 address for this host.'
#               ' Don\'t really know what to do...')
#         return -1, None
#     else:
#         mylog('MY IPV6\'s ARE {}'.format(ipv6_addresses), '35')
#
#     ipv6_addr = ipv6_addresses[0]  # arbitrarily take the first one
#
#     # todo: I think we can take the IP out of this message.
#     # This message is only used to create a new host model in the remote.
#     # The host that we're going to connect to doesn't need to know this.
#     # msg = NewHostMessage(ipv6_addr
#     #                      , instance.host_port
#     #                      , instance.host_ws_port
#     #                      , platform.uname()[1])
#     msg = NewHostMessage('0'
#                          , 0
#                          , 0
#                          , platform.uname()[1])
#     raw_conn.send_obj(msg)
#
#     resp_obj = raw_conn.recv_obj()
#     check_response(ASSIGN_HOST_ID, resp_obj.type)
#
#     my_id = resp_obj.id
#     mylog('Remote says my id is {}'.format(my_id))
#     # I have no idea wtf to do with this.
#     key = resp_obj.key
#     mylog('Remote says my key is {}'.format(key))
#     cert = resp_obj.cert
#     mylog('Remote says my cert is {}'.format(cert))
#
#     sslSocket.close()
#     return 0, my_id  # returning a status code as well...
#     # I've been in kernel land too long, haven't I...


def request_cloud(instance, remote, cloud, test_enabled, db):
    # type: (NebsInstance, Remote, Cloud, bool, SimpleDB) -> ResultAndData
    full_name = cloud.full_name()
    if test_enabled:
        print('please enter username for {}:'.format(full_name))
        username = stdin.readline()[:-1]
        print('Enter the password for {}:'.format(full_name))
        password = stdin.readline()[:-1]  # todo this is yea, bad.
    else:
        username = raw_input('Enter the username for {}:'.format(full_name)).lower()
        print('Enter the password for {}:'.format(full_name))
        password = getpass.getpass()

    rd = remote.setup_socket()
    if not rd.success:
        return rd
    raw_conn = RawConnection(rd.data)

    msg = RequestCloudMessage(remote.my_id_from_remote, cloud.uname(), cloud.cname(), username, password)
    raw_conn.send_obj(msg)

    return finish_request_cloud(instance, remote, cloud, db, raw_conn)


def client_request_cloud(instance, remote, cloud, session_id, db):
    # type: (NebsInstance, Remote, Cloud, str, SimpleDB) -> ResultAndData

    rd = remote.setup_socket()
    if not rd.success:
        return rd
    raw_conn = RawConnection(rd.data)

    msg = ClientMirrorMessage(session_id, remote.my_id_from_remote, cloud.uname(), cloud.cname())
    raw_conn.send_obj(msg)

    return finish_request_cloud(instance, remote, cloud, db, raw_conn)


def finish_request_cloud(instance, remote, cloud, db, connection):
    # type: (NebsInstance, Remote, Cloud, SimpleDB, AbstractConnection) -> ResultAndData
    resp_obj = connection.recv_obj()
    if resp_obj.type == INVALID_STATE:
        rd = Error(resp_obj.message)
    elif resp_obj.type == MIRROR_FAILURE:
        rd = Error(resp_obj.message)
    elif resp_obj.type == AUTH_ERROR:
        rd = Error('Failed to authenticate with the remote')
    elif resp_obj.type == GO_RETRIEVE_HERE:
        rd = handle_go_retrieve(instance, resp_obj, remote, cloud, db)
        # attempt_wakeup()
    else:
        rd = Error('Unidentified error {} while mirroring'.format(resp_obj.type))
    # if not rd.success:
    #     mylog(rd.data)
    return rd


def handle_go_retrieve(instance, response, remote, cloud, db):
    # type: (NebsInstance, GoRetrieveHereMessage, Remote, Cloud, SimpleDB) -> ResultAndData
    _log = get_mylog()
    check_response(GO_RETRIEVE_HERE, response.type)
    other_address = response.ip
    other_port = response.port
    requester_id = response.requester_id
    other_id = response.other_id
    max_size = response.max_size

    cloud.my_id_from_remote = requester_id
    cloud.max_size = max_size
    db.session.add(cloud)
    remote.clouds.append(cloud)

    if other_address == '0' and other_port == 0:
        _log.debug('No other hosts in cloud')
        # note: falling out of this function takes us to the code that
        #       sends the MIRRORING_COMPLETE message.
        # Set up the private data for this cloud. We do this here, because this
        #   sentinel case (== no other hosts) means that no other host has
        # created a .nebs file yet, so we're responsible.
        owner_ids = response.owner_ids
        private_data = PrivateData(cloud, owner_ids)
        # just instantiating the private data is enough to write the backend
        cloud.last_sync = datetime.utcnow()
        rd = cloud.create_file(os.path.join(cloud.root_directory, '.nebs'), db=db, timestamp=None)
        rd.data.last_sync = datetime.utcnow()
        db.session.commit()
        # TODO: I'm not using that rd above, that's not intentional, I don't know why.
        return Success(cloud.id)

    _log.debug('requesting host at [{}]({},{})'.format(other_id, other_address, other_port))
    is_ipv6 = ':' in other_address
    sock_type = socket.AF_INET6 if is_ipv6 else socket.AF_INET
    sock_addr = (other_address, other_port, 0, 0) if is_ipv6 else (other_address, other_port)

    host_sock = socket.socket(sock_type, socket.SOCK_STREAM)
    host_sock.connect(sock_addr)
    host_conn = RawConnection(host_sock)
    # host_sock = setup_remote_socket(other_address, other_port)
    # todo:8 initialize our ssl context here

    cloud_uname = cloud.uname()
    cname = cloud.cname()
    my_id = cloud.my_id_from_remote
    msg = HostHostFetchMessage(my_id, other_id, cloud_uname, cname, '/')

    db.session.commit()
    cloud_id = cloud.id
    # db.session.close()
    # db = None

    host_conn.send_obj(msg)
    _log.debug('Sent HOST_HOST_FETCH as a mirror request.')
    _log.debug('Sent {}'.format(msg.serialize()))

    resp_obj = host_conn.recv_obj()

    # db = instance.get_db()
    # cloud = db.session.query(Cloud).get(cloud_id)
    resp_type = resp_obj.type

    rd = Error()
    if resp_type == HOST_VERIFY_HOST_FAILURE:
        _log.debug('Other host failed to verify our request, "{}"'.format(resp_obj.message), '31')
    elif resp_type != HOST_FILE_TRANSFER:
        _log.debug('Other host did not respond successfully, \n\t response was="{}"'.format(resp_obj))
    else:
        # Here we recv a whole bunch of files from the host
        recv_file_tree(None, resp_obj, cloud, host_conn, db)
        db.session.commit()

        rd = Success(cloud_id)
    _log.debug('Bottom of go_retrieve')
    return rd


def complete_mirroring(db, cloud):
    # type: (SimpleDB, Cloud) -> ResultAndData
    _log = get_mylog()
    rd = setup_remote_socket(cloud)
    if rd.success:
        new_rem_sock = rd.data
        remote_conn = RawConnection(new_rem_sock)
        msg = MirroringCompleteMessage(cloud.my_id_from_remote, cloud.uname(), cloud.cname())
        remote_conn.send_obj(msg)

        cloud.completed_mirroring = True
        db.session.commit()

        new_rem_sock.close()
    else:
        msg = 'Failed to complete_mirroring {}'.format(rd.data)
        _log.error(msg)
    return rd


def attempt_wakeup(instance):
    # type: (NebsInstance) -> None
    # TODO: M0.4 - Suport multiple mirrors
    _log = get_mylog()
    _log.debug('Attempting to alert any existing nebs')
    my_addr = instance.get_existing_ip()
    port = instance.get_existing_port()

    if port is not None and my_addr is not None:
        try:
            local_sock = socket.socket
            is_ipv6 = ':' in my_addr
            sock_type = socket.AF_INET6 if is_ipv6 else socket.AF_INET
            sock_addr = (my_addr, port, 0, 0) if is_ipv6 else (my_addr, port)

            host_sock = socket.socket(sock_type, socket.SOCK_STREAM)
            host_sock.connect(sock_addr)
            _log.debug('connected to a nebs')
            conn = RawConnection(host_sock)
            msg = RefreshMessageMessage()
            conn.send_obj(msg)
            _log.debug('refreshed host')
            conn.recv_obj()
            conn.close()
        except Exception, e:
            _log.debug('Failed to alert any other hosts on this machine:')
            _log.debug(e.message)
    # todo: Will this work with miniupnp?
    # try:
    #     local_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    #     ips = get_ipv6_list()
    #     ip = ips[0]
    #     mylog('Local IP6 is {}'.format(ip))
    #     local_sock.connect((ip, instance.host_port, 0, 0))
    #     mylog('connected to a nebs')
    #     conn = RawConnection(local_sock)
    #     msg = RefreshMessageMessage()
    #     conn.send_obj(msg)
    #     mylog('refreshed host')
    #     conn.recv_obj()
    #     conn.close()
    # except Exception, e:
    #     mylog('Failed to alert any other hosts on this machine')


def acquire_remote(instance, address, port, disable_ssl=False):
    # type: (NebsInstance, str, int) -> ResultAndData
    _log = get_mylog()
    db = instance.get_db()
    net_controller = NetworkController(instance)
    net_controller.refresh_external_ip()

    new_key = create_key_pair(crypto.TYPE_RSA, 2048)
    ip = net_controller.get_external_ip()
    req = create_cert_request(new_key, CN=ip)
    certificate_request_string = crypto.dump_certificate_request(crypto.FILETYPE_PEM, req)
    message = HostMoveRequestMessage(INVALID_HOST_ID, ip, certificate_request_string)
    _log.debug('Initializing ssl connection to remote')
    rd = setup_ssl_socket_for_address(address, port)
    if rd.success:
        ssl_socket = rd.data
        raw_conn = RawConnection(ssl_socket)
        _log.debug('Acquiring remote... (sending initial CSR for {})'.format(ip))
        raw_conn.send_obj(message)
        resp_obj = raw_conn.recv_obj()
        if resp_obj.type == HOST_MOVE_RESPONSE:
            remote = Remote()
            remote.set_certificate(ip, resp_obj.crt)
            remote.my_id_from_remote = resp_obj.host_id
            remote.key = crypto.dump_privatekey(crypto.FILETYPE_PEM, new_key)
            remote.remote_address = address
            remote.remote_port = port
            db.session.add(remote)
            rd = Success(remote)
        else:
            msg = 'Failed to create the new host with the remote - got bad response.'
            _log.error(msg)
            _log.debug('response was "{}"'.format(resp_obj.serialize()))
            rd = Error(msg)
    return rd


def locate_remote(instance, address, port, disable_ssl=False):
    # type: (NebsInstance, str, int) -> ResultAndData
    _log = get_mylog()
    rd = lookup_remote(instance.get_db(), address, port)
    if rd.success:
        remote = rd.data
        if remote is not None:
            rd = Success(remote)
        else:
            rd = acquire_remote(instance, address, port, disable_ssl=disable_ssl)
    _log.debug('Found remote for {},{}'.format(address, port))
    return rd



def _do_mirror(instance, remote_address, remote_port, cloud_uname, cloudname, directory, session_id, test=False, disable_ssl=False):
    _log = get_mylog()
    rd = locate_remote(instance, remote_address, remote_port, disable_ssl=disable_ssl)
    if not rd.success:
        return Error('Failed to locate the remote for remote address "{}:{}"'.format(remote_address, remote_port))
    remote = rd.data

    real_root = './{}/{}'.format(cloud_uname, cloudname) if directory is None else directory
    abs_root = os.path.abspath(real_root)
    print('Mirroing into {}'.format(abs_root))
    if not os.path.exists(abs_root):
        try:
            os.makedirs(abs_root)
        except Exception as e:
            return Error('Failed to create the directory {}'.format(abs_root))
    elif not os.path.isdir(abs_root):
        return Error('target ({}) should be a directory'.format(real_root))
    elif not (len(os.listdir(abs_root)) == 0):
        return Error('Target directory should be empty')

    _log.debug('attempting to get cloud named "{}" from remote at [{}]:{} into '
               'root directory <{}>'.format(cloudname, remote_address, remote_port, abs_root))

    cloud = Cloud(cloud_uname, cloudname, abs_root)

    # At this point, the cloud is not yet in the DB.
    rd = Error()
    db = instance.get_db()
    if session_id is None:
        rd = request_cloud(instance, remote, cloud, test, db)
    else:
        rd = client_request_cloud(instance, remote, cloud, session_id, db)
    _log.debug('finished requesting cloud')

    if rd.success:
        _log.debug('Created cloud\'s ID={}'.format(rd.data))
        created_cloud = db.session.query(Cloud).get(rd.data)
        rd = complete_mirroring(db, created_cloud)

    if rd.success:
        sleep(1)
        # try waking up any hosts on this machine that this mirror should be tracked by.
        attempt_wakeup(instance)

    # todo goto code that checks if a nebs.start process is running
    _log.debug('nebs reached bottom of mirror()')
    return rd


# TODO: Allow clouds to be mirrored to non-empty directories if there isn't
#       another mirror already.
# Or maybe we have a different command, like `init` that creates a cloud from a
#       working directory. That could be a good idea! TODO
DIRECTORY_HELP_TEXT = 'Provide a directory to mirror into. \n'\
                      'If you omit this parameter, the mirror will create a path' \
                      ' for the cloud in the current working directory, under ' \
                      '"./<username>/<cloudname>."\n'\
                      'If you provide a directory, it must be empty.'


class MirrorCommand(BaseCommand):

    def add_parser(self, subparsers):
        mirror = subparsers.add_parser('mirror', description='mirror a cloud to this device')
        mirror.add_argument('remote'
                            , help='URL of the remote host to connect to. Don\'t include the port in this string, use the -p option.')
        mirror.add_argument('-p', '--port'
                            , help='Port on the remote to connect to. Defaults to {}'.format(REMOTE_PORT)
                            , default=REMOTE_PORT)
        mirror.add_argument('-d', '--directory'
                            , help=DIRECTORY_HELP_TEXT)
        mirror.add_argument('-s', '--session-id'
                            , help='Optionally provide a session ID to bypass the authentication prompt')
        # TODO: remove this arg entirely. The tests should be using sids
        mirror.add_argument('--test'
                            , action='store_true'
                            , help='Used for testing - forces the  password prompt to be in plaintext.')
        mirror.add_argument('cloud_name', metavar='cloud-name'
                            , help='Name of the cloud to mirror, in <username>/<cloudname> format')
        return mirror

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        # Namespace(access=None, cloud_name='foo/bar', command='mirror',
        #   directory=None, func=<function mirror_with_args at 0x000000000998D518>,
        #   instance=None, log=None, port=12345, remote='localhost', session_id=None,
        #   test=False, verbose=None, working_dir=None)
        remote_address = args.remote
        cloud_name = args.cloud_name
        directory = args.directory
        remote_port = int(args.port)
        session_id = args.session_id
        test = args.test
        if cloud_name.find('/') == -1:
            print('mirror: error: cloud name must be in the format <username>/<cloudname>')
            return
        uname_cname = cloud_name.split('/')
        uname = uname_cname[0]
        cname = uname_cname[1]

        if len(uname) < 1 or len(cname) < 1:
            print('mirror: error: cloud name must be in the format <username>/<cloudname>')
            return

        # if disable_ssl:
        #     print('Disabling SSL when connecting to the remote. This should not be used outside of nebula development')

        rd = _do_mirror(instance, remote_address, remote_port, uname, cname, directory, session_id, test, disable_ssl=False)
        if not rd.success:
            print(rd.data)
        else:
            print('Successfully mirrored {}. Use `nebr.py start` to start the nebula server.'.format(cloud_name))
        return rd
