import sys
import socket
from threading import Thread

from OpenSSL.SSL import SysCallError
from OpenSSL import SSL


# from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
# from models import Base
from remote import remote_db
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
    new_user_instance = User()
    new_user_instance.name = 'fake'
    new_user_instance.created_on = datetime.utcnow()
    remote_db.session.add(new_user_instance)
    remote_db.session.commit()
    print 'There are now ', remote_db.session.query(User).count(), 'users'


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






