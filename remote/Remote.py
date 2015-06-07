from threading import Thread
from OpenSSL.SSL import SysCallError

__author__ = 'Mike'

import socket
from OpenSSL import SSL

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 12345              # Arbitrary non-privileged port


context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('key')
context.use_certificate_file('cert')


def filter_func(connection, address):
    inc_data = connection.recv(1024)
    print 'The message type is[', inc_data, ']'
    echo_func(connection,address)


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


if __name__ == '__main__':

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




