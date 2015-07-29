import sys
import os
import socket
from threading import Thread
from werkzeug.security import generate_password_hash, \
     check_password_hash
import getpass
from OpenSSL.SSL import SysCallError
from OpenSSL import SSL


# print sys.executable
sys.path.append(os.path.join(sys.path[0], '..'))
# todo this is a dirty hack, I'm sure.
# print sys.path
# It's so I can access the 'remote' module one dir up.
# regarding dirty hack status, it's /better/ now, not great.

from datetime import datetime

from remote import remote_db as db
from remote import User, Cloud, Host

__author__ = 'Mike'
###############################################################################

###############################################################################

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 12345              # Arbitrary non-privileged port

###############################################################################


def filter_func(connection, address):
    inc_data = connection.recv(1024)
    print 'The message type is[', inc_data, ']'
    echo_func(connection, address)


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
    s.listen(5)
    while True:
        (connection, address) = s.accept()

        print 'Connected by', address
        # spawn a new thread to handle this connection
        thread = Thread(target=filter_func, args=[connection, address])
        thread.start()
        # echo_func(connection, address)
    pass


def new_user(argv):
    print 'here we\'ll make a new user'

    email = raw_input('Enter an email for the new user: ').lower()
    # todo validate that this is in fact an email
    already_exists = User.query.filter_by(email=email).first()
    if already_exists:
        print 'A user already exists with that email address.'
        return

    username = raw_input('Enter a username for the new user: ').lower()
    already_exists = User.query.filter_by(username=username).first()
    if already_exists:
        print 'A user already exists with that username.'
        return

    name = raw_input('Enter a name for the new user: ').lower()
    password = getpass.getpass('Enter a password for the new user: ').lower()
    password_again = getpass.getpass('Enter the password (again): ').lower()

    if password != password_again:
        print 'The passwords entered didn\'t match'
        return

    new_user_instance = User(
        email=email
        , username=username
        , password=generate_password_hash(password)
        , name=name
        , created_on=datetime.utcnow()
    )
    db.session.add(new_user_instance)
    db.session.commit()
    print 'There are now ', User.query.count(), 'users'


def create(argv):
    """Creates a new cloud in the db to be tracked. Needs the credentials of the
    User who owns it."""
    print 'Creating a new cloud. First, enter credentials for the owner'
    owner_uname = raw_input('Enter the owner\'s username: ')
    owner_pass = getpass.getpass('Enter the owner\'s password: ')
    owner = User.query.filter_by(username=owner_uname).first()

    if (owner is None) or (not (check_password_hash(owner.password, owner_pass))):
        print 'username/password combination invalid.'
        return
    cloud_name_in = raw_input('Please enter the name of the new cloud: ')
    owned_clouds_dups_check = owner.owned_clouds\
        .filter_by(name=cloud_name_in)\
        .first()
    contributed_clouds_dups_check = owner.contributed_clouds\
        .filter_by(name=cloud_name_in)\
        .first()
    if (owned_clouds_dups_check is not None) \
            or (contributed_clouds_dups_check is not None):
        print owner.name, 'already has a cloud named', cloud_name_in
        return
    max_size = raw_input(
        'Enter a max size for the cloud in bytes' +
        ' (leave blank to default to 4 MB(4000000)'
    )
    if max_size is None:
        max_size = 4000000
    else:
        max_size = int(max_size)
    create_cloud(owner_uname, owner_pass, cloud_name_in, max_size)
    print 'Successfully created the', cloud_name_in, 'cloud for', owner_uname

def create_cloud(username, password, cloudname, max_size):
    owner = User.query.filter_by(username=username).first()
    if (owner is None) or (not (check_password_hash(owner.password, password))):
        raise Exception('Owner username/password combination invalid.')
    owned_clouds_dups_check = owner.owned_clouds\
        .filter_by(name=cloudname)\
        .first()
    contributed_clouds_dups_check = owner.contributed_clouds\
        .filter_by(name=cloudname)\
        .first()
    if (owned_clouds_dups_check is not None) \
            or (contributed_clouds_dups_check is not None):
        raise Exception(owner.name, 'already has a cloud named', cloudname)

    if max_size is None:
        max_size = 4000000
    new_cloud = Cloud(
        name=cloudname
        , created_on=datetime.utcnow()
        , last_update=datetime.utcnow()
        , max_size=max_size
    )
    db.session.add(new_cloud)
    new_cloud.owners.append(owner)
    new_cloud.contributors.append(owner)
    db.session.commit()


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






