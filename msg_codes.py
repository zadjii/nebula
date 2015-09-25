from _ctypes import sizeof
import json
import os
import struct
import sys

__author__ = 'zadjii'
UNPREPARED_HOST_ERROR = -3
AUTH_ERROR = -2
GENERIC_ERROR = -1
NEW_HOST_MSG = 0
ASSIGN_HOST_ID = 1
HOST_HANDSHAKE = 2
REMOTE_HANDSHAKE = 3
REM_HANDSHAKE_GO_FETCH = 4
REQUEST_CLOUD = 5
GO_RETRIEVE_HERE = 6
PREPARE_FOR_FETCH = 7
HOST_HOST_FETCH = 8
HOST_FILE_TRANSFER = 9
MAKE_CLOUD_REQUEST = 10
MAKE_CLOUD_RESPONSE = 11
MAKE_USER_REQUEST = 12
MAKE_USER_RESPONSE = 13
MIRRORING_COMPLETE = 14
GET_HOSTS_REQUEST = 15
GET_HOSTS_RESPONSE = 16
COME_FETCH = 17
REMOVE_FILE = 18
HOST_FILE_PUSH = 19
STAT_FILE_REQUEST = 20
STAT_FILE_RESPONSE = 21
LIST_FILES_REQUEST = 22
LIST_FILES_RESPONSE = 23
READ_FILE_REQUEST = 24
READ_FILE_RESPONSE = 25


def send_unprepared_host_error_and_close(socket):
    send_msg(json.dumps(make_msg(UNPREPARED_HOST_ERROR)), socket)
    socket.close()


def send_generic_error_and_close(socket):
    send_msg(json.dumps(make_msg(GENERIC_ERROR)), socket)
    socket.close()


def recv_msg(socket):
    """Gets a json msg from the socket specified, and decodes into a dict
        for us."""
    data = socket.recv(8)
    size = decode_msg_size(data)
    # print 'decoding msg length {}->{}'.format(data, size)
    # todo a while loop to read all the data into a buffer
    buff = socket.recv(size)
    # print 'recv\'d into {}B[2]'.format(len(buff))
    return decode_msg(buff)


def write_msg(msg_json, socket):
    # print 'writing message {}.{}.{}.\'{}\''.format(
    #     len(msg_json)
    #     , get_msg_size(msg_json)
    #     , decode_msg_size(get_msg_size(msg_json))
    #     , msg_json)
    socket.write(get_msg_size(msg_json))
    socket.write(msg_json)


def send_msg(msg_json, socket):
    # print 'sending message {}.{}.{}.\'{}\''.format(
    #     len(msg_json)
    #     , get_msg_size(msg_json)
    #     , decode_msg_size(get_msg_size(msg_json))
    #     , msg_json)
    socket.send(get_msg_size(msg_json))
    socket.send(msg_json)


def get_msg_size(msg_json):
    size = len(msg_json)
    return struct.pack('Q', size)


def decode_msg_size(long_long):
    return struct.unpack('Q', long_long)[0]


def make_msg(msg_type):
    return {'type': msg_type}


def decode_msg(msg):
    # print 'decoding\'{}\''.format(msg)
    obj = json.loads(msg)
    return obj


def make_new_host_json(port):
    msg = make_msg(NEW_HOST_MSG)
    msg['port'] = port
    return json.dumps(msg)


def make_assign_host_id_json(host_id, key, cert):
    msg = make_msg(ASSIGN_HOST_ID)
    msg['id'] = host_id
    msg['key'] = 'TODO placeholder key'
    msg['cert'] = 'TODO placeholder cert'
    return json.dumps(msg)


def make_host_handshake_json(host_id, listening_port, last_update):
    msg = make_msg(HOST_HANDSHAKE)
    msg['id'] = host_id
    msg['port'] = listening_port
    msg['update'] = last_update
    return json.dumps(msg)


def make_request_cloud_json(host_id, cloudname, username, password):
    msg = make_msg(REQUEST_CLOUD)
    msg['id'] = host_id
    msg['cname'] = cloudname
    msg['uname'] = username
    msg['pass'] = password
    return json.dumps(msg)


def make_prepare_for_fetch_json(host_id, cloudname, ip):
    msg = make_msg(PREPARE_FOR_FETCH)
    msg['id'] = host_id
    msg['cname'] = cloudname
    msg['ip'] = ip
    return json.dumps(msg)


def make_go_retrieve_here_json(host_id, ip, port):
    msg = make_msg(GO_RETRIEVE_HERE)
    msg['id'] = host_id  # todo maybe unneeded.
    msg['ip'] = ip
    msg['port'] = port
    return json.dumps(msg)


def make_host_host_fetch(host_id, cloudname, requested_root):
    msg = make_msg(HOST_HOST_FETCH)
    msg['id'] = host_id
    msg['cname'] = cloudname
    msg['root'] = requested_root
    return json.dumps(msg)


def make_host_file_transfer(host_id, cloudname, relative_pathname, is_dir, filesize):
    msg = make_msg(HOST_FILE_TRANSFER)
    msg['id'] = host_id
    msg['cname'] = cloudname
    msg['fpath'] = relative_pathname
    msg['fsize'] = filesize
    msg['isdir'] = is_dir
    return json.dumps(msg)


def make_mirroring_complete(host_id, cloudname):
    msg = make_msg(MIRRORING_COMPLETE)
    msg['id'] = host_id
    msg['cname'] = cloudname
    return json.dumps(msg)


def make_get_hosts_request(host_id, cloudname):
    msg = make_msg(GET_HOSTS_REQUEST)
    msg['id'] = host_id
    msg['cname'] = cloudname
    # todo needs uniquely identifying info, so that not just anyone
    # cont can get all the other hosts ip/ports
    return json.dumps(msg)


def make_get_hosts_response(cloud):
    msg = make_msg(GET_HOSTS_RESPONSE)
    msg['cname'] = cloud.name
    hosts = cloud.hosts.all()
    host_jsons = []
    for host in hosts:
        host_obj = {
            'ip': host.ip
            , 'port': host.port
            , 'id': host.id
            , 'update': host.last_update
            , 'hndshk': host.last_handshake
        }
        host_jsons.append(host_obj)
    msg['hosts'] = host_jsons
    return json.dumps(msg)

#
# def make_come_fetch(host_id, port, cloudname, updated_file):
#     msg = make_msg(COME_FETCH)
#     msg['id'] = host_id  # The id of the recipient
#     msg['port'] = port  # my address, don't need ip, they'll get that from the connection
#     msg['cname'] = cloudname
#     msg['root'] = updated_file
#     return json.dumps(msg)


def make_remove_file(host_id, cloudname, updated_file):
    msg = make_msg(REMOVE_FILE)
    msg['id'] = host_id  # The id of the recipient
    msg['cname'] = cloudname
    msg['root'] = updated_file
    return json.dumps(msg)


def make_host_file_push(tgt_host_id, cloudname, updated_file):
    msg = make_msg(HOST_FILE_PUSH)
    msg['tid'] = tgt_host_id
    msg['cname'] = cloudname
    msg['fpath'] = updated_file
    return json.dumps(msg)


def make_stat_dict(file_path):
    """You should make sure file exists before calling this."""
    if file_path is None:
        return None
    if not os.path.exists(file_path):
        return None
    file_path = os.path.normpath(file_path)
    file_stat = os.stat(file_path)
    stat_dict = {
        'atime': file_stat.st_atime
        , 'mtime': file_stat.st_mtime
        , 'ctime': file_stat.st_ctime
        , 'inode': file_stat.st_ino
        , 'mode': file_stat.st_mode
        , 'dev': file_stat.st_dev
        , 'nlink': file_stat.st_nlink
        , 'uid': file_stat.st_uid
        , 'gid': file_stat.st_gid
        , 'size': file_stat.st_size
        , 'name': os.path.basename(file_path)
    }
    return stat_dict


def make_stat_request(cloudname, rel_path):
    msg = make_msg(STAT_FILE_REQUEST)
    msg['cname'] = cloudname
    msg['fpath'] = rel_path
    return json.dumps(msg)


def make_stat_response(cloudname, rel_path, file_path):
    msg = make_msg(STAT_FILE_RESPONSE)
    msg['cname'] = cloudname
    msg['fpath'] = rel_path
    msg['stat'] = make_stat_dict(file_path)
    return json.dumps(msg)


def make_ls_array(file_path):
    """You should make sure file exists before calling this."""
    if file_path is None:
        return None
    if not os.path.exists(file_path):
        return None
    file_path = os.path.normpath(file_path)
    subdirs = []
    for f in os.listdir(file_path):
        subdirs.append(make_stat_dict(f))
    return subdirs


def make_list_files_request(cloudname, rel_path):
    msg = make_msg(LIST_FILES_REQUEST)
    msg['cname'] = cloudname
    msg['fpath'] = rel_path
    return json.dumps(msg)


def make_list_files_response(cloudname, rel_path, file_path):
    msg = make_msg(LIST_FILES_RESPONSE)
    msg['cname'] = cloudname
    msg['fpath'] = rel_path
    msg['stat'] = make_stat_dict(file_path)
    msg['ls'] = make_ls_array(file_path)
    return json.dumps(msg)

