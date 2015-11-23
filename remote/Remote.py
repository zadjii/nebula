import sys
import os


import socket
from threading import Thread
from OpenSSL.SSL import SysCallError
from OpenSSL import SSL
from connections.RawConnection import RawConnection
from host.util import set_mylog_name, mylog
from messages.ClientGetCloudsResponse import ClientGetCloudsResponse
from remote.function.client_session_setup import setup_client_session,\
    get_cloud_host
from remote.function.new_user import new_user
from remote.function.create import create

from msg_codes import *
from messages import *

from remote import User, Cloud, Host, get_db, Session

__author__ = 'Mike'

###############################################################################

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 12345              # Arbitrary non-privileged port

KEY_FILE = 'remote/key'
CERT_FILE = 'remote/cert'
# todo this is jank AF
###############################################################################


def filter_func(connection, address):
    msg_obj = connection.recv_obj()
    msg_type = msg_obj.type
    # print 'The message is', msg_obj
    if msg_type == NEW_HOST_MSG:
        new_host_handler(connection, address, msg_obj)
    elif msg_type == REQUEST_CLOUD:
        host_request_cloud(connection, address, msg_obj)
    elif msg_type == MIRRORING_COMPLETE:
        mirror_complete(connection, address, msg_obj)
    elif msg_type == GET_HOSTS_REQUEST:
        respond_to_get_hosts_request(connection, address, msg_obj)
    elif msg_type == CLIENT_SESSION_REQUEST:
        setup_client_session(connection, address, msg_obj)
    elif msg_type == CLIENT_GET_CLOUDS_REQUEST:
        respond_to_get_clouds(connection, address, msg_obj)
    elif msg_type == CLIENT_GET_CLOUD_HOST_REQUEST:
        get_cloud_host(connection, address, msg_obj)
    else:
        print 'I don\'t know what to do with', msg_obj
    connection.close()


def respond_to_get_clouds(connection, address, msg_obj):
    db = get_db()
    session_id = msg_obj.sid
    sess_obj = db.session.query(Session).filter_by(uuid=session_id).first()
    if sess_obj is None:
        # fixme send error
        mylog('CGCR: no session? {}'.format(session_id))
        return
    user = sess_obj.user
    if user is None:
        # fixme return error
        mylog('CGCR: no user? {}'.format(sess_obj.user_id))
        return
    mylog('getting clouds for {}'.format(user.username))
    owned_names = [c.name for c in user.owned_clouds.all()]
    contributed_names = [c.name for c in user.contributed_clouds.all()]
    msg = ClientGetCloudsResponse(
        session_id
        , owned_names
        , contributed_names
    )
    connection.send_obj(msg)


def respond_to_get_hosts_request(connection, address, msg_obj):
    db = get_db()
    host_id = msg_obj.id
    cloudname = msg_obj.cname

    matching_host = db.session.query(Host).get(host_id)
    if matching_host is None:
        send_generic_error_and_close(connection)
        raise Exception('There was no host with the ID[{}], wtf'.format(host_id))

    matching_cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if matching_cloud is None:
        send_generic_error_and_close(connection)
        raise Exception('No cloud with name ' + cloudname)

    # send_msg(make_get_hosts_response(matching_cloud), connection)
    msg = GetHostsResponseMessage(matching_cloud)
    connection.send_obj(msg)
    print 'responded to Host[{}] asking for hosts of \'{}\''\
        .format(host_id, cloudname)


def mirror_complete(connection, address, msg_obj):
    db = get_db()
    host_id = msg_obj.id
    cloudname = msg_obj.cname

    matching_host = db.session.query(Host).get(host_id)
    if matching_host is None:
        send_generic_error_and_close(connection)
        raise Exception('There was no host with the ID[{}], wtf'.format(host_id))

    matching_cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if matching_cloud is None:
        send_generic_error_and_close(connection)
        raise Exception('No cloud with name ' + cloudname)

    matching_cloud.hosts.append(matching_host)
    db.session.commit()
    print 'Host[{}] finished mirroring cloud \'{}\''.format(host_id, cloudname)


def host_request_cloud(connection, address, msg_obj):
    db = get_db()
    host_id = msg_obj.id
    cloudname = msg_obj.cname
    username = msg_obj.uname
    password = msg_obj.passw

    print('User provided {},{},{},{}'.format(
        host_id, cloudname, username, password
    ))
    matching_host = db.session.query(Host).get(host_id)
    if matching_host is None:
        send_generic_error_and_close(connection)
        raise Exception('There was no host with the ID[{}], wtf'.format(host_id))

    match = db.session.query(Cloud).filter_by(name=cloudname).first()
    if match is None:
        send_generic_error_and_close(connection)
        raise Exception('No cloud with name ' + cloudname)

    user = db.session.query(User).filter_by(username=username).first()
    if user is None:
        send_generic_error_and_close(connection)
        print [owner.username for owner in match.owners.all()]
        raise Exception(username + ' is not an owner of ' + cloudname)
    # todo validate their password
    # Here we've established that they are an owner.
    # print 'Here, they will have successfully been able to mirror?'
    ip = '0'
    port = 0
    rand_host = match.hosts.first()  #todo make this random
    if rand_host is not None:
        prep_for_fetch_msg = make_prepare_for_fetch_json(host_id, cloudname, address[0])
        rand_host.send_msg(prep_for_fetch_msg)
        # ip = rand_host.ip
        # port = rand_host.port
        # print 'rand host is ({},{})'.format(ip, port)
        # context = SSL.Context(SSL.SSLv23_METHOD)
        # context.use_privatekey_file(KEY_FILE)
        # context.use_certificate_file(CERT_FILE)
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #
        # # s = SSL.Connection(context, s)
        # # whatever fuck it lets just assume it's good todo
        #
        # s.connect((ip, port))
        # send_msg(prep_for_fetch_msg, s)
        # print 'nebr completed talking to rand_host'
        # s.close()
    msg = GoRetrieveMessage(0, ip, port)
    connection.send_obj(msg)
    # send_msg(make_go_retrieve_here_json(0, ip, port), connection)

    print 'nebr has reached the end of host_request_cloud'


def new_host_handler(connection, address, msg_obj):
    db = get_db()
    print 'Handling new host'
    host = Host()
    host.ip = address[0]
    host.port = msg_obj.port
    db.session.add(host)
    db.session.commit()

    msg = AssignHostIDMessage(host.id, 'todo_placeholder_key', 'todo_placeholder_cert')
    connection.send_obj(msg)
    # send_msg(
    #     make_assign_host_id_json(host.id, 'todo_placeholder_key', 'todo_placeholder_cert')
    #     , connection
    # )


def start(argv):
    set_mylog_name('nebr')
    context = SSL.Context(SSL.SSLv23_METHOD)
    context.use_privatekey_file(KEY_FILE)
    context.use_certificate_file(CERT_FILE)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = SSL.Connection(context, s)
    s.bind((HOST, PORT))
    mylog('Listening on ({},{})'.format(HOST, PORT))

    s.listen(5)
    while True:
        (connection, address) = s.accept()
        raw_connection = RawConnection(connection)
        mylog('Connected by {}'.format(address))
        # spawn a new thread to handle this connection
        thread = Thread(target=filter_func, args=[raw_connection, address])
        thread.start()
        thread.join()
        # echo_func(connection, address)
        # todo: possible that we might want to thread.join here.
        # cont  Make it so that each req gets handled before blindly continuing


def list_users(argv):
    db = get_db()
    # users = User.query.all()
    users = db.session.query(User).all()
    print 'There are ', len(users), 'users.'
    print '[{}] {:16} {:16}'.format('id', 'name', 'email')
    for user in users:
        print '[{}] {:16} {:16}'.format(user.id, user.name, user.email)


def list_clouds(argv):
    db = get_db()
    # clouds = Cloud.query.all()
    clouds = db.session.query(Cloud).all()
    print 'There are ', len(clouds), 'clouds.'
    print '[{}] {:16} {:16} {:16}'.format('id', 'name', 'max_size', 'owners')
    for cloud in clouds:
        owners = ''
        for owner in cloud.owners:
            owners = owners + owner.name + ' '
        print '[{}] {:16} {:16} {}'\
            .format(cloud.id, cloud.name, cloud.max_size, owners)


commands = {
    'new-user': new_user
    , 'start': start
    , 'create': create
    , 'list-users': list_users
    , 'list-clouds': list_clouds
}
command_descriptions = {
    'new-user': '\tadd a new user to the database'
    , 'start': '\t\tstart the remote server'
    , 'create': '\t\tcreate a new cloud to track'
    , 'list-users': '\tlist all current users'
    , 'list-clouds': '\tlist all current clouds'
}


def usage():
    print 'usage: nebr <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]


def nebr_main(argv):
    if len(argv) < 2:
        usage()
        sys.exit(0)

    command = argv[1]

    selected = commands.get(command, usage)
    selected(argv[2:])
    sys.exit(0)


if __name__ == '__main__':
    nebr_main(sys.argv)
