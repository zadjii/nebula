import sys
import socket
from threading import Thread
from werkzeug.security import generate_password_hash, \
     check_password_hash
import getpass
from OpenSSL.SSL import SysCallError
from OpenSSL import SSL

import sys; print(sys.executable)
import os; print(os.getcwd())

from datetime import datetime

from remote import remote_db as db
from remote import User

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
            print '>>> There was an exception in Remote.echo_func, receiving data'
            break

    connection.close()
    print 'connection to ' + str(address) + ' closed, ayy lmao'


def usage():
    print 'neb-remote [new-user start init]'


def start():

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


def new_user():
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


def init():
    pass


if __name__ == '__main__':

    # if there weren't any args, print the usage and return
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)

    command = sys.argv[1]
    commands = {
        'new-user': new_user
        , 'start': start
        , 'init': init
    }
    selected = commands.get(command, usage)
    selected()
    sys.exit(0)






