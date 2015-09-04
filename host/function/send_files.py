import os
from stat import S_ISDIR
from msg_codes import send_msg, make_host_file_transfer

__author__ = 'Mike'


def send_tree(other_id, cloud, requested_root, connection):
    print 'They requested the file', requested_root
    # find the file on the system, get it's size.
    requesting_all = requested_root == '/'
    filepath = None
    # if the root is '/', send all of the children of the root
    if requesting_all:
        filepath = cloud.root_directory
    else:
        filepath = os.path.join(cloud.root_directory, requested_root)
    print 'The translated request path was {}'.format(filepath)
    send_file_to_other(other_id, cloud, filepath, connection)
    complete_sending_files(other_id, cloud, filepath, connection)
    connection.close()


def send_file_to_other(other_id, cloud, filepath, socket_conn):
    """
    Assumes that the other host was already verified, and the cloud is non-null
    """
    req_file_stat = os.stat(filepath)
    relative_pathname = os.path.relpath(filepath, cloud.root_directory)
    print 'relative path for {} in cloud {} is {}'.format(filepath, cloud.name, relative_pathname)
    req_file_is_dir = S_ISDIR(req_file_stat.st_mode)
    if req_file_is_dir:
        send_msg(
            make_host_file_transfer(
                other_id
                , cloud.name
                , relative_pathname
                , req_file_is_dir
                , 0
            )
            , socket_conn
        )
        for f in os.listdir(filepath):
            send_file_to_other(other_id, cloud, os.path.join(filepath, f), socket_conn)
    else:
        req_file_size = req_file_stat.st_size
        requested_file = open(filepath, 'rb')
        send_msg(
            make_host_file_transfer(
                other_id
                , cloud.name
                , relative_pathname
                , req_file_is_dir
                , req_file_size
            )
            , socket_conn
        )
        l = 1
        while l:
            new_data = requested_file.read(1024)
            l = socket_conn.send(new_data)
            print 'Sent {}B of file data'.format(l)
        requested_file.close()


def complete_sending_files(other_id, cloud, filepath, socket_conn):
    send_msg(
        make_host_file_transfer(other_id, cloud.name, None, None, None)
        , socket_conn
    )