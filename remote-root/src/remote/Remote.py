import sys
import os


sys.path.append(os.path.join(sys.path[0], '..'))
import socket
from threading import Thread
from OpenSSL.SSL import SysCallError
from OpenSSL import SSL
from remote.function.new_user import new_user
from remote.function.create import create

from remote.msg_codes import *

# print sys.executable

# todo this is a dirty hack, I'm sure.
# print sys.path
# It's so I can access the 'remote' module one dir up.
# regarding dirty hack status, it's /better/ now, not great.

from remote import User, Cloud, Host
from remote import remote_db as db

__author__ = 'Mike'
###############################################################################

###############################################################################

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 12345              # Arbitrary non-privileged port

###############################################################################

def filter_func(connection, address):
    inc_data = connection.recv(1024)
    print 'The message type is[', inc_data, ']'
    if int(inc_data) == NEW_HOST_MSG:
        new_host_handler(connection, address)
    elif int(inc_data) == REQUEST_CLOUD:
        host_request_cloud(connection, address)
    else:
        print 'I don\'t know what to do with [', inc_data, ']'

        # echo_func(connection, address)
    connection.close()


def host_request_cloud(connection, address):

    host_id = int(connection.recv(1024))
    cloudname_length = int(connection.recv(1024))
    cloudname = connection.recv(cloudname_length)
    username = connection.recv(1024)
    password = connection.recv(1024)
    print('User provided {},{},{},{},{}'.format(
        host_id, cloudname_length, cloudname, username, password
    ))
    matching_host = Host.query.get(host_id)
    if matching_host is None:
        raise Exception('There was no host with the ID[{}], wtf'.format(host_id))

    match = Cloud.query.filter_by(name=cloudname).first()
    if match is None:
        raise Exception('No cloud with name ' + cloudname)
    user = match.owners.filter_by(username=username).first()
    if user is None:
        raise Exception(username + ' is not an owner of ' + cloudname)
    # Here we've established that they are an owner.
    # print 'Here, they will have successfully been able to mirror?'
    ip = '0'
    port = '0'
    rand_host = match.hosts.first()
    if rand_host is not None:
        ip = rand_host.ip
        port = 23456
        print 'rand host is ({},{})'.format(ip, port)
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.use_privatekey_file('key')
        context.use_certificate_file('cert')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # s = SSL.Connection(context, s)
        # whatever fuck it lets just assume it's good

        s.connect((ip, port))
        # lol wtf does this even work
        # s.send(str(PREPARE_FOR_FETCH))
        # s.send(str(host_id))
        # s.send(str(cloudname))
        # s.send(str(address[0]))
        # fuck it json everything
        json_msg = '{"type":'+str(PREPARE_FOR_FETCH)+',"id":'+str(host_id)+',"name":"'+cloudname+'","ip":"'+address[0]+'"}'
        s.send(json_msg)
        print 'nebr completed talking to rand_host'

    connection.send(str(GO_RETRIEVE_HERE))
    connection.send(str(ip))
    connection.send(str(port))  # yolo
    match.hosts.append(matching_host)
    db.session.commit()
    print 'nebr has reached the end of host_request_cloud'
    connection.close()


def new_host_handler(connection, address):
    print 'Handling new host'
    host = Host()
    host.ip = address[0]
    host.port = address[1] # todo this actually isn't right.
    # cont the host needs to tell the remote what port it's listening on.
    # cont till then, I'll just assume its 23456 cause YOLO
    db.session.add(host)
    db.session.commit()

    connection.send(str(ASSIGN_HOST_ID))
    connection.send(str(host.id))
    connection.send(str(address[0]))  # todo: placeholder key
    connection.send(str(address[1]))  # todo: placeholder cert


def echo_func(connection, address):
    inc_data = connection.recv(1024)
    while inc_data:
        # if not inc_data:
        #     break
        print inc_data
        connection.sendall(inc_data)
        # break
        # inc_data = connection.recv(1024)

        try:
            inc_data = connection.recv(1024)
        except SysCallError:
            print '>>There was an exception in Remote.echo_func, receiving data'
            break

    connection.close()
    print 'connection to ' + str(address) + ' closed, ayy lmao'


def start(argv):

    context = SSL.Context(SSL.SSLv23_METHOD)
    context.use_privatekey_file('key')
    context.use_certificate_file('cert')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = SSL.Connection(context, s)
    s.bind((HOST, PORT))
    print 'Listening on ({},{})'.format(HOST, PORT)

    s.listen(5)
    while True:
        (connection, address) = s.accept()

        print 'Connected by', address
        # spawn a new thread to handle this connection
        thread = Thread(target=filter_func, args=[connection, address])
        thread.start()
        # echo_func(connection, address)


def list_users(argv):
    users = User.query.all()
    print 'There are ', len(users), 'users.'
    print '[{}] {:16} {:16}'.format('id', 'name', 'email')
    for user in users:
        print '[{}] {:16} {:16}'.format(user.id, user.name, user.email)


def list_clouds(argv):
    clouds = Cloud.query.all()
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
    print 'usage: neb-remote <command>'
    print ''
    print 'The available commands are:'
    for command in command_descriptions.keys():
        print '\t', command, command_descriptions[command]


if __name__ == '__main__':

    # if there weren't any args, print the usage and return
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)

    command = sys.argv[1]

    selected = commands.get(command, usage)
    selected(sys.argv[2:])
    sys.exit(0)






