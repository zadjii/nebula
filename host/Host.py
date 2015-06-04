import os
import time
import socket
import ssl

__author__ = 'Mike'


filename = 'C:\\tmp\\touchme.txt'
HOST = 'localhost'
PORT = 12345

if __name__ == '__main__':

    last_modified = os.stat(filename).st_mtime

    print last_modified

    while True:
        now_modified = os.stat(filename).st_mtime
        if now_modified > last_modified:
            print filename, ' was modified at ', now_modified, ', last ', last_modified
            last_modified = now_modified
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            sslSocket = ssl.wrap_socket(s)
            sslSocket.write(filename + ' was modified at ' + str(now_modified))
            data = sslSocket.recv(4096)
            print repr(data)
            s.close()
        else:
            time.sleep(1)

    # s.connect((HOST, PORT))
    #
    # sslSocket = ssl.wrap_socket(s)
    #
    # sslSocket.write('Hello secure socket\n')
    # data = sslSocket.recv(4096)
    # print repr(data)
    # s.close()