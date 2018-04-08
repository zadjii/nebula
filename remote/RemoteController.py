import atexit
import logging
import socket
from datetime import datetime

from OpenSSL import SSL, crypto
from OpenSSL.crypto import X509Extension
from werkzeug.security import generate_password_hash

from common.SimpleDB import SimpleDB
from common_util import *
from connections.AbstractConnection import AbstractConnection
from connections.RawConnection import RawConnection
from messages import *
from msg_codes import *
from remote import User, Host
from remote.NebrInstance import NebrInstance
from remote.function.client import respond_to_client_get_cloud_hosts
from remote.function.client_session_setup import setup_client_session, \
    get_cloud_host, host_verify_client, do_client_get_cloud_host
from remote.function.get_hosts import get_hosts_response
from remote.function.mirror import mirror_complete, host_request_cloud, \
    client_mirror, host_verify_host
from remote.models.CloudLink import CloudLink
from remote.models.Mirror import Mirror
from remote.util import get_user_from_session, validate_session_id, \
    get_cloud_by_name, get_user_by_name

__author__ = 'Mike'

###############################################################################

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 12345              # Arbitrary non-privileged port

# KEY_FILE = 'remote/key'
# CERT_FILE = 'remote/cert'
# todo this is jank AF
###############################################################################


def host_handshake(remote_obj, connection, address, msg_obj):
    _log = get_mylog()
    db = remote_obj.get_db()
    ipv6 = msg_obj.ipv6
    # host = db.session.query(Host).get(msg_obj.id)
    mirror = db.session.query(Mirror).get(msg_obj.id)
    host = mirror.host
    if host is not None:
        if not host.ipv6 == ipv6:
            # mylog('Host [{}] moved from "{}" to "{}"'.format(host.id, host.ipv6, ipv6))
            _log.debug('Host [{}] moved from "{}" to "{}"'.format(host.id, host.ipv6, ipv6))
        host.ipv6 = ipv6
        host.port = msg_obj.port
        host.ws_port = msg_obj.wsport
        mirror.remaining_size = msg_obj.remaining_space
        mirror.curr_size = msg_obj.used_space
        host.hostname = msg_obj.hostname
        mirror.last_handshake = datetime.utcnow()
        db.session.commit()


def client_session_refresh(remote_obj, connection, address, msg_obj):
    _log = get_mylog()
    db = remote_obj.get_db()
    session_id = msg_obj.sid
    # refreshes the session
    rd = validate_session_id(db, session_id)
    # db.session.commit()

    if not rd.success:
        _log.warning('Remote failed to refresh session {}, "{}"'.format(session_id, rd.data))
    # This particular message doesn't want a response


def do_client_get_clouds(db, session_id):
    # type: (SimpleDB, str) -> ResultAndData
    # type: (SimpleDB, str) -> ResultAndData(True, ([dict], [dict]) )
    # type: (SimpleDB, str) -> ResultAndData(False, BaseMessage )
    _log = get_mylog()
    rd = get_user_from_session(db, session_id)
    if not rd.success:
        msg = 'generic CGCHsR error: "{}"'.format(rd.data)
        _log.error(msg)
        return Error(InvalidStateMessage(msg))
    else:
        user = rd.data

    _log.debug('getting clouds for {}'.format(user.username))

    owned_clouds = [c.to_dict() for c in user.owned_clouds.all()]
    contributed_clouds = [c.to_dict() for c in user.contributed_clouds.all()]
    _log.debug('{}'.format(contributed_clouds))
    return Success((owned_clouds, contributed_clouds))


def do_add_user(db, name, username, password, email):
    # type: (SimpleDB) -> ResultAndData
    # type: (SimpleDB) -> ResultAndData(True, int)
    # type: (SimpleDB) -> ResultAndData(False, BaseMessage )
    _log = get_mylog()
    if (username is None) or (password is None) or (email is None):
        return Error(InvalidStateMessage('Must provide username, password and email'))

    user = get_user_by_name(db, username)
    if user is not None:
        return Error(InvalidStateMessage('Username already taken'))
    user = db.session.query(User).filter_by(email=email).first()
    if user is not None:
        return Error(InvalidStateMessage('Email already taken'))

    user = User()
    user.name = name
    user.username = username
    user.password = generate_password_hash(password)
    user.email = email
    user.created_on = datetime.utcnow()

    db.session.add(user)
    db.session.commit()

    _log.info('Added new user {}'.format(user.username))

    return Success(user.id)


def respond_to_get_clouds(remote_obj, connection, address, msg_obj):
    db = remote_obj.get_db()
    session_id = msg_obj.sid
    rd = do_client_get_clouds(db, session_id)
    if rd.success:
        owned_clouds = rd.data[0]
        contributed_clouds = rd.data[1]
        msg = ClientGetCloudsResponseMessage(
            session_id
            , owned_clouds
            , contributed_clouds
        )
        connection.send_obj(msg)
    else:
        connection.send_obj(rd.data)


def new_host_handler(remote_obj, connection, address, msg_obj):
    db = remote_obj.get_db()
    mylog('Handling new host')
    host = Host()
    # host.ipv4 = address[0]
    host.ipv6 = msg_obj.ipv6
    host.port = msg_obj.port
    db.session.add(host)
    db.session.commit()

    msg = AssignHostIdMessage(host.id, 'todo_placeholder_key', 'todo_placeholder_cert')
    connection.send_obj(msg)


def client_add_owner(remote_obj, connection, address, msg_obj):
    # type: (RemoteController, AbstractConnection, object, ClientAddOwnerMessage) -> None

    if not msg_obj.type == CLIENT_ADD_OWNER:
        msg = 'Somehow tried to client_add_owner without CLIENT_ADD_OWNER'
        err = InvalidStateMessage(msg)
        send_error_and_close(err, connection)
        return

    db = remote_obj.get_db()
    session_id = msg_obj.sid
    cloudname = msg_obj.cname
    cloud_uname = msg_obj.cloud_uname
    new_user_id = msg_obj.new_user_id

    rd = validate_session_id(db, session_id)
    if not rd.success:
        err = AddOwnerFailureMessage(rd.data)
        send_error_and_close(err, connection)
        return
    else:
        sess_obj = rd.data
        user = sess_obj.user

    if new_user_id == PUBLIC_USER_ID:
        msg = 'The public can\'t be a owner of a cloud'
        err = AddOwnerFailureMessage(msg)
        mylog(err.message, '31')
        send_error_and_close(err, connection)
        return

    cloud = get_cloud_by_name(db, cloud_uname, cloudname)
    if cloud is None:
        msg = 'No matching cloud {}'.format((cloud_uname, cloudname))
        err = AddOwnerFailureMessage(msg)
        send_error_and_close(err, connection)
        return

    if not cloud.has_owner(user):
        msg = 'User "{}" is not an owner of the cloud "{}"'.format(user.username, (cloud_uname, cloudname))
        err = AddOwnerFailureMessage(msg)
        send_error_and_close(err, connection)
        return
    new_owner = db.session.query(User).get(new_user_id)
    if new_owner is None:
        msg = 'No matching user {}'.format(new_user_id)
        err = AddOwnerFailureMessage(msg)
        send_error_and_close(err, connection)
        return

    cloud.add_owner(new_owner)
    db.session.commit()
    response = AddOwnerSuccessMessage(session_id, new_user_id, cloud_uname, cloudname)
    connection.send_obj(response)
    connection.close()


def do_host_move(remote_obj, host, ip, csr):
    # type: (RemoteController, Host, str, crypto.X509Req) -> ResultAndData
    new_cert = remote_obj.sign_host_csr(csr, ip)
    host.last_certificate = crypto.dump_certificate(crypto.FILETYPE_PEM, new_cert)
    return Success(host)


def host_move(remote_obj, connection, address, msg_obj):
    # type: (RemoteController, AbstractConnection, object, HostMoveRequestMessage) -> None
    _log = get_mylog()
    if not msg_obj.type == HOST_MOVE_REQUEST:
        msg = 'Somehow tried to host_move without HOST_MOVE_REQUEST'
        err = InvalidStateMessage(msg)
        _log.debug(msg)
        send_error_and_close(err, connection)
        return
    db = remote_obj.get_db()

    host_id = msg_obj.my_id
    ip = msg_obj.ip
    csr = msg_obj.csr

    if host_id == INVALID_HOST_ID:
        host = Host()
        db.session.add(host)
        db.session.commit()
        msg = 'Created new host entry [{}] for ip "{}"'.format(host.id, host.ip())
        _log.debug(msg)
    else:
        host = db.session.query(Host).get(host_id)
    if host is None:
        msg = 'Could not find a host matching id {} during host_move'.format(host_id)
        err = InvalidStateMessage(msg)
        _log.debug(msg)
        send_error_and_close(err, connection)

    certificate_request = crypto.load_certificate_request(crypto.FILETYPE_PEM, csr)
    rd = do_host_move(remote_obj, host, ip, certificate_request)
    if rd.success:
        host = rd.data
        new_host_id = host.id
        new_host_crt = host.last_certificate + open(remote_obj.nebr_instance.get_cert_file(), 'rt').read()
        response = HostMoveResponseMessage(new_host_id, new_host_crt)
        connection.send_obj(response)
    else:
        msg = rd.data if rd.data is not None else 'Unknown error while moving host'
        err = InvalidStateMessage(msg)
        _log.debug(msg)
        send_error_and_close(err, connection)

    pass


def host_add_contributor(remote_obj, connection, address, msg_obj):
    # type: (RemoteController, AbstractConnection, object, AddContributorMessage) -> None
    _log = get_mylog()
    if not msg_obj.type == ADD_CONTRIBUTOR:
        msg = 'Somehow tried to host_add_contributor without ADD_CONTRIBUTOR'
        err = InvalidStateMessage(msg)
        send_error_and_close(err, connection)
        return
    mylog('host_add_contributor')
    db = remote_obj.get_db()
    host_id = msg_obj.host_id
    cloudname = msg_obj.cname
    cloud_uname = msg_obj.cloud_uname
    new_user_id = msg_obj.new_user_id

    cloud = get_cloud_by_name(db, cloud_uname, cloudname)
    if cloud is None:
        msg = 'No matching cloud {}'.format((cloud_uname, cloudname))
        err = AddContributorFailureMessage(msg)
        send_error_and_close(err, connection)
        return
    source_mirror = cloud.mirrors.filter_by(id=host_id).first()
    # source_host = cloud.hosts.filter_by(id=host_id).first()
    if source_mirror is None:
        msg = 'No matching mirror {}'.format(host_id)
        err = AddContributorFailureMessage(msg)
        send_error_and_close(err, connection)
        return

    is_public = new_user_id == PUBLIC_USER_ID
    if is_public:
        # Make sure the cloud is a publicly available cloud
        cloud.make_public()
    else:
        new_owner = db.session.query(User).get(new_user_id)
        if new_owner is None:
            msg = 'No matching user {}'.format(new_user_id)
            err = AddContributorFailureMessage(msg)
            send_error_and_close(err, connection)
            return
        cloud.add_contributor(new_owner)

    db.session.commit()
    response = AddContributorSuccessMessage(new_user_id, cloud_uname, cloudname)
    mylog('host_add_contributor success')
    connection.send_obj(response)
    connection.close()


################################################################################
def host_reserve_link(remote_obj, connection, address, msg_obj):
    # type: (RemoteController, AbstractConnection, object, AddContributorMessage) -> None
    _log = get_mylog()
    db = remote_obj.get_db()
    if not msg_obj.type == HOST_RESERVE_LINK_REQUEST:
        msg = 'Somehow tried to host_reserve_link without HOST_RESERVE_LINK_REQUEST'
        err = InvalidStateMessage(msg)
        send_error_and_close(err, connection)
        return
    cloudname = msg_obj.cname
    cloud_uname = msg_obj.cloud_uname
    rd = do_host_reserve_link(db, cloud_uname, cloudname)
    if rd.success:
        link = rd.data
        response = HostReserveLinkResponseMessage(link.link_string)
    else:
        response = rd.data
    connection.send_obj(response)
    connection.close()


def do_host_reserve_link(db, uname, cname):
    # type: (SimpleDB, str, str) -> ResultAndData
    # type: (SimpleDB, str, str) -> ResultAndData(True, CloudLink)
    # type: (SimpleDB, str, str) -> ResultAndData(False, BaseMessage)
    cloud = get_cloud_by_name(db, uname, cname)
    if cloud is None:
        msg = 'No matching cloud {}'.format((uname, cname))
        err = InvalidStateMessage(msg)
        return Error(err)
    link = CloudLink(cloud, db)
    db.session.add(link)
    db.session.commit()
    return Success(link)
################################################################################
def client_get_link_host(remote_obj, connection, address, msg_obj):
    # type: (RemoteController, AbstractConnection, object, AddContributorMessage) -> None
    _log = get_mylog()
    db = remote_obj.get_db()
    if not msg_obj.type == CLIENT_GET_LINK_HOST:
        msg = 'Somehow tried to client_get_link_host without CLIENT_GET_LINK_HOST'
        err = InvalidStateMessage(msg)
        send_error_and_close(err, connection)
        return

    link_string = msg_obj.link_string
    sid = msg_obj.sid
    rd = do_client_get_link_host(db, link_string, sid)
    if rd.success:
        host_mapping = rd.data
        mirror = host_mapping.mirror
        host = mirror.host
        cloud = mirror.cloud
        response = ClientGetCloudHostResponseMessage(sid, cloud.uname(), cloud.cname(), host.ipv6,
                                                     host.port, host.ws_port)
    else:
        response = rd.data
    connection.send_obj(response)
    connection.close()


def do_client_get_link_host(db, link_string, session_id):
    # type: (SimpleDB, str) -> ResultAndData
    # type: (SimpleDB, str) -> ResultAndData(True, ClientCloudHostMapping)
    # type: (SimpleDB, str) -> ResultAndData(False, BaseMessage)
    link = db.session.query(CloudLink).filter_by(link_string=link_string).first()
    if link is None:
        msg = 'No matching link {}'.format(link_string)
        err = InvalidStateMessage(msg)
        return Error(err)

    cloud = link.cloud
    if cloud is None:
        msg = 'No matching cloud for link {}'.format(link_string)
        err = InvalidStateMessage(msg)
        return Error(err)

    return do_client_get_cloud_host(db, cloud.uname(), cloud.cname(), session_id)

################################################################################


class RemoteController(object):
    def __init__(self, nebr_instance):
        # type: (NebrInstance) -> None
        self.nebr_instance = nebr_instance

    def get_db(self):
        # type: () -> SimpleDB
        """
        Note: that Remote::get_db returns a new instance of SimpleDB, because
          the remote spawns a new child thread for each connection.
        In the long run, this isn't a great idea. especially because remote
          interactions should be short lived in general...

        :return:
        """
        return self.nebr_instance.make_db_session()

    def start(self, argv):
        set_mylog_name('nebr')
        _log = get_mylog()
        enable_vt_support()

        if not os.path.exists(self.nebr_instance.get_key_file()):
            msg = 'SSL Key file "{}" does not exist'.format(self.nebr_instance.get_key_file())
            _log.error(msg)
            return Error(msg)
        if not os.path.exists(self.nebr_instance.get_cert_file()):
            msg = 'SSL Certificate file "{}" does not exist'.format(self.nebr_instance.get_cert_file())
            _log.error(msg)
            return Error(msg)

        _log.info('Loaded SSL key and cert')

        # register the shutdown callback
        atexit.register(self.shutdown)

        force_kill = '--force' in argv
        if force_kill:
            mylog('Forcing shutdown of previous instance')
        rd = self.nebr_instance.start(force_kill)
        if rd.success:
            self.network_updates()

    def network_updates(self):
        _log = get_mylog()
        # context = SSL.Context(SSL.SSLv23_METHOD)
        context = SSL.Context(SSL.TLSv1_2_METHOD)
        mylog(self.nebr_instance.get_key_file())
        mylog(self.nebr_instance.get_cert_file())
        context.use_privatekey_file(self.nebr_instance.get_key_file())
        context.use_certificate_file(self.nebr_instance.get_cert_file())

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s = SSL.Connection(context, s)
        address = (HOST, PORT)  # ipv4
        attempts = 0
        succeeded = False
        while attempts < 5 and not succeeded:
            attempts += 1
            try:
                s.bind(address)
                succeeded = True
            except Exception, e:
                _log.error('Failed to bind to address, {}'.format(e.message))
        if not succeeded:
            return Error('Failed to bind to network (is the socket already in use?)')


        _log = get_mylog()
        _log.info('Listening on {}'.format(address))

        s.listen(5)
        while True:
            (connection, address) = s.accept()
            raw_connection = RawConnection(connection)
            _log.debug('Connected by {}'.format(address))

            try:
                self.filter_func(raw_connection, address)
            except Exception, e:
                _log.error('Error handling connection')
                _log.error(e.message)

            # echo_func(connection, address)
            # todo: possible that we might want to thread.join here.
            # cont  Make it so that each req gets handled before blindly continuing
        _log.error('Fell out the bottom of the while(true) in RemoteController.network_updates')

    def filter_func(self, connection, address):
        msg_obj = connection.recv_obj()
        msg_type = msg_obj.type
        # print 'The message is', msg_obj
        if msg_type == NEW_HOST:
            new_host_handler(self, connection, address, msg_obj)
        elif msg_type == HOST_HANDSHAKE:
            host_handshake(self, connection, address, msg_obj)
        elif msg_type == REQUEST_CLOUD:
            host_request_cloud(self, connection, address, msg_obj)
        elif msg_type == MIRRORING_COMPLETE:
            mirror_complete(self, connection, address, msg_obj)
        elif msg_type == GET_HOSTS_REQUEST:
            get_hosts_response(self, connection, address, msg_obj)
        elif msg_type == GET_ACTIVE_HOSTS_REQUEST:
            get_hosts_response(self, connection, address, msg_obj)
        elif msg_type == CLIENT_SESSION_REQUEST:
            setup_client_session(self, connection, address, msg_obj)
        elif msg_type == CLIENT_GET_CLOUDS_REQUEST:
            respond_to_get_clouds(self, connection, address, msg_obj)
        elif msg_type == CLIENT_GET_CLOUD_HOST_REQUEST:
            get_cloud_host(self, connection, address, msg_obj)
        elif msg_type == CLIENT_GET_CLOUD_HOSTS_REQUEST:
            respond_to_client_get_cloud_hosts(self, connection, address, msg_obj)
        elif msg_type == CLIENT_MIRROR:
            client_mirror(self, connection, address, msg_obj)
        elif msg_type == HOST_VERIFY_CLIENT_REQUEST:
            host_verify_client(self, connection, address, msg_obj)
        elif msg_type == HOST_VERIFY_HOST_REQUEST:
            host_verify_host(self, connection, address, msg_obj)
        elif msg_type == CLIENT_ADD_OWNER:
            client_add_owner(self, connection, address, msg_obj)
        elif msg_type == ADD_CONTRIBUTOR:
            host_add_contributor(self, connection, address, msg_obj)
        elif msg_type == CLIENT_SESSION_REFRESH:
            client_session_refresh(self, connection, address, msg_obj)
        elif msg_type == HOST_MOVE_REQUEST:
            host_move(self, connection, address, msg_obj)
        elif msg_type == HOST_RESERVE_LINK_REQUEST:
            host_reserve_link(self, connection, address, msg_obj)
        elif msg_type == CLIENT_GET_LINK_HOST:
            client_get_link_host(self, connection, address, msg_obj)
        else:
            print 'I don\'t know what to do with', msg_obj
        connection.close()

    def shutdown(self):
        mylog('RemoteController.shutdown')
        if self.nebr_instance is not None:
            self.nebr_instance.shutdown()

    def sign_host_csr(self, certificate_request, ip):
        # type: (crypto.X509Req, str) -> crypto.X509
        my_key = crypto.load_privatekey(crypto.FILETYPE_PEM, open(self.nebr_instance.get_key_file(), 'rt').read())
        my_crt = crypto.load_certificate(crypto.FILETYPE_PEM, open(self.nebr_instance.get_cert_file(), 'rt').read())

        not_after = 60 * 60 * 24 * 365 * 1  # one year, totally arbitrary

        cert = crypto.X509()
        cert.set_version(2)
        epoch = datetime.utcfromtimestamp(0)
        now = datetime.utcnow()
        total_seconds = int((now - epoch).total_seconds())
        cert.set_serial_number(total_seconds)  # todo: Add  some method for actually tracking serial numbers
        cert.gmtime_adj_notBefore(0)  # these values are seconds from the moment of signing
        cert.gmtime_adj_notAfter(not_after)  # these values are seconds from the moment of signing
        cert.set_issuer(my_crt.get_subject())
        cert.set_subject(certificate_request.get_subject())
        cert.set_pubkey(certificate_request.get_pubkey())

        basic = X509Extension(b'basicConstraints', False, b'CA:false')
        alt = X509Extension(b'subjectAltName', False, b'IP.1:{}'.format(ip))
        cert.add_extensions([basic, alt])
        cert.sign(my_key, 'sha256')
        return cert
