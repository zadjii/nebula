import os
import sys
import time
import socket
import ssl

from stat import *

__author__ = 'Mike'


default_filename = 'C:\\tmp\\touchme.txt'
default_root_path = 'C:/tmp/root-0'

HOST = 'localhost'
PORT = 12345

file_tree_root = {}
modified_files = []


def dict_walktree(top, callback, root_struct):
    """recursively descend the directory tree rooted at top,
       calling the callback function for each regular file"""

    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        file_stat = os.stat(pathname)
        mode = file_stat.st_mode
        curr_modified = file_stat.st_mtime
        visiting_node = None

        # first, see if the tree already has a node for this file.
        # if so, check it's mtime, and if modified, add it to the list of updates.
        for node in root_struct['children']:
            if node['path'] == pathname:
                visiting_node = node
                break
        if visiting_node is not None:
            if curr_modified > visiting_node['last_modified']:
                visiting_node['last_modified'] = curr_modified
                modified_files.append(visiting_node)
        # else create a new node.
        else:
            visiting_node = {'last_modified': curr_modified, 'path': pathname, 'children': []}
            root_struct['children'].append(visiting_node)


        if S_ISDIR(mode):  # It's a directory, recurse into it
            # use the directory's node as the new root.
            dict_walktree(pathname, callback, visiting_node)
        elif S_ISREG(mode):  # It's a file, call the callback function
            callback(visiting_node['path'])
        else:  # Unknown file type, print a message
            print 'Skipping %s' % pathname


def visit_file(filename):
    # print 'visiting', filename
    pass




if __name__ == '__main__':
    root_path = sys.argv[1] if len(sys.argv) > 1 else default_root_path

    last_modified = os.stat(default_filename).st_mtime

    print last_modified

    file_tree_root['last_modified'] = last_modified
    file_tree_root['path'] = root_path
    file_tree_root['children'] = []

    while True:
        modified_files = []
        dict_walktree(root_path, visit_file, file_tree_root)
        if len(modified_files) > 0:
            print str(len(modified_files)) + ' file(s) were modified.'
        # now_modified = os.stat(default_filename).st_mtime
        # if now_modified > last_modified:
        #     print default_filename, ' was modified at ', now_modified, ', last ', last_modified
        #     last_modified = now_modified
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            sslSocket = ssl.wrap_socket(s)
            sslSocket.write(str(-1))  # placeholder message type
            num_sent = 0
            for file_node in modified_files:
                sslSocket.write(file_node['path'] + ' was modified at ' + str(file_node['last_modified']))
                num_sent += 1
            # sslSocket.write(default_filename + ' was modified at ' + str(now_modified))
            pulling = True
            num_recvd = 0
            while pulling and (num_recvd < num_sent):
                data = sslSocket.recv(1024)
                if not data:
                    pulling = False
                print 'remote responded['+str(len(data))+']: ' + repr(data)
                num_recvd += 1
            # sslSocket.unwrap()
            # sslSocket.close()
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        else:
            print 'No updates'
        time.sleep(1)

    # s.connect((HOST, PORT))
    #
    # sslSocket = ssl.wrap_socket(s)
    #
    # sslSocket.write('Hello secure socket\n')
    # data = sslSocket.recv(4096)
    # print repr(data)
    # s.close()