import socket
from datetime import datetime
from threading import Thread

from OpenSSL import SSL
from werkzeug.security import generate_password_hash

from common_util import send_error_and_close, Success, Error, enable_vt_support
from common_util import set_mylog_name, mylog
from connections.RawConnection import RawConnection
from messages import *
from msg_codes import *
from remote import User, Host
from remote.NebrInstance import NebrInstance
from remote.function.client import respond_to_client_get_cloud_hosts
from remote.function.client_session_setup import setup_client_session,\
    get_cloud_host, host_verify_client
from remote.function.get_hosts import get_hosts_response
from remote.function.mirror import mirror_complete, host_request_cloud, \
    client_mirror, host_verify_host
from remote.util import get_user_from_session, validate_session_id, \
    get_cloud_by_name

__author__ = 'Mike'

###############################################################################

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 12345              # Arbitrary non-privileged port

KEY_FILE = 'remote/key'
CERT_FILE = 'remote/cert'
# todo this is jank AF
###############################################################################


def host_handshake(remote_obj, connection, address, msg_obj):
    db = remote_obj.get_db()
    ipv6 = msg_obj.ipv6
    host = db.session.query(Host).get(msg_obj.id)
    if host is not None:
        if not host.ipv6 == ipv6:
            mylog('Host [{}] moved from "{}" to "{}"'.format(host.id, host.ipv6, ipv6))
        host.ipv6 = ipv6
        host.port = msg_obj.port
        host.ws_port = msg_obj.wsport
        host.last_handshake = datetime.utcnow()
        db.session.commit()


def client_session_refresh(remote_obj, connection, address, msg_obj):
    db = remote_obj.get_db()
    session_id = msg_obj.sid
    # refreshes the session
    rd = validate_session_id(db, session_id)
    # db.session.commit()

    if not rd.success:
        mylog('Remote failed to refresh session {}, "{}"'.format(session_id, rd.data))
    # This particular message doesn't want a response


def do_client_get_clouds(db, session_id):
    # type: (SimpleDB, str) -> ResultAndData
    # type: (SimpleDB, str) -> ResultAndData(True, ([dict], [dict]) )
    # type: (SimpleDB, str) -> ResultAndData(False, BaseMessage )
    rd = get_user_from_session(db, session_id)
    if not rd.success:
        msg = 'generic CGCHsR error: "{}"'.format(rd.data)
        mylog(msg, '31')
        return Error(InvalidStateMessage(msg))
    else:
        user = rd.data

    mylog('getting clouds for {}'.format(user.username))

    owned_clouds = [c.to_dict() for c in user.owned_clouds.all()]
    contributed_clouds = [c.to_dict() for c in user.contributed_clouds.all()]
    return Success((owned_clouds, contributed_clouds))


def do_add_user(db, username, password, email):
    # type: (SimpleDB) -> ResultAndData
    # type: (SimpleDB) -> ResultAndData(True, int)
    # type: (SimpleDB) -> ResultAndData(False, BaseMessage )
    if (username is None) or (password is None) or (email is None):
        return Error(InvalidStateMessage('Must provide username, password and email'))

    user = db.session.query(User).filter_by(username=username).first()
    if user is not None:
        return Error(InvalidStateMessage('Username already taken'))
    user = db.session.query(User).filter_by(email=email).first()
    if user is not None:
        return Error(InvalidStateMessage('Email already taken'))

    user = User()
    user.username = username
    user.password = generate_password_hash(password)
    user.email = email
    user.created_on = datetime.utcnow()

    db.session.add(user)
    db.session.commit()

    mylog('Added new user {}'.format(user.username))

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
    print 'Handling new host'
    host = Host()
    host.ipv4 = address[0]
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


def host_add_contributor(remote_obj, connection, address, msg_obj):
    # type: (RemoteController, AbstractConnection, object, AddContributorMessage) -> None
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
    source_host = cloud.hosts.filter_by(id=host_id).first()
    if source_host is None:
        msg = 'No matching host {}'.format(host_id)
        err = AddContributorFailureMessage(msg)
        send_error_and_close(err, connection)
        return
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


class RemoteController(object):
    def __init__(self, nebr_instance):
        # type: (NebrInstance) -> RemoteController
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
        enable_vt_support()
        context = SSL.Context(SSL.SSLv23_METHOD)
        mylog(self.nebr_instance.get_key_file())
        mylog(self.nebr_instance.get_cert_file())
        context.use_privatekey_file(self.nebr_instance.get_key_file())
        context.use_certificate_file(self.nebr_instance.get_cert_file())
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s = SSL.Connection(context, s)
        address = (HOST, PORT)  # ipv4
        # address = (HOST, PORT, 0, 0) # ipv6
        s.bind(address)
        mylog('Listening on {}'.format(address))

        s.listen(5)
        while True:
            (connection, address) = s.accept()
            raw_connection = RawConnection(connection)
            mylog('Connected by {}'.format(address))
            # This is kinda really dumb.
            # I guess the thread just catches any exceptions and prevents the main
            #   from crashing, otherwise it has no purpose.
            # spawn a new thread to handle this connection

            # thread = Thread(target=self.filter_func, args=[raw_connection, address])
            # thread.start()
            # thread.join()

            self.filter_func(raw_connection, address)

            # echo_func(connection, address)
            # todo: possible that we might want to thread.join here.
            # cont  Make it so that each req gets handled before blindly continuing

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
        else:
            print 'I don\'t know what to do with', msg_obj
        connection.close()

