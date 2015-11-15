import json
import os


__author__ = 'zadjii'
FILE_IS_NOT_DIR_ERROR = -5
FILE_IS_DIR_ERROR = -4
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

CLIENT_SESSION_REQUEST = 26  # C->R
CLIENT_SESSION_ALERT = 27  # R->H
CLIENT_SESSION_RESPONSE = 28  # R->C

CLIENT_FILE_PUT = 29  # C->H
CLIENT_FILE_TRANSFER = 30  # C->H

CLIENT_GET_CLOUDS_REQUEST = 31  # C->R
CLIENT_GET_CLOUDS_RESPONSE = 32  # R->C
CLIENT_GET_CLOUD_HOST_REQUEST = 33
CLIENT_GET_CLOUD_HOST_RESPONSE = 34


def send_msg_and_close(message_dict, socket):
    send_msg(json.dumps(message_dict), socket)
    socket.close()


def send_file_is_not_dir_error_and_close(filename, socket):
    msg = make_msg(FILE_IS_NOT_DIR_ERROR)
    msg['path'] = filename
    send_msg_and_close(msg, socket)


def send_file_is_dir_error_and_close(filename, socket):
    msg = make_msg(FILE_IS_DIR_ERROR)
    msg['path'] = filename
    send_msg_and_close(msg, socket)


def send_unprepared_host_error_and_close(socket):
    send_msg_and_close(make_msg(UNPREPARED_HOST_ERROR), socket)


def send_generic_error_and_close(socket):
    send_msg_and_close(make_msg(GENERIC_ERROR), socket)


# def recv_msg(socket):
#     pass
#     """Gets a json msg from the socket specified, and decodes into a dict
#         for us."""
#     # data = memoryview(bytearray(b" " * 8))
#     data = socket.recv(8)
#     # size = 0
#     # while size < 8:
#     #     size = size + socket.recv_into(data[size:], 8 - size)
#
#     size = decode_msg_size(data)
#     # print 'decoding msg length {}->{}'.format(data, size)
#     # todo a while loop to read all the data into a buffer
#     buff = socket.recv(size)
#     # print 'recv\'d into {}B[2]'.format(len(buff))
#     return decode_msg(buff)
#
#
# def write_msg(msg_json, socket):
#     # print 'writing message {}.{}.{}.\'{}\''.format(
#     #     len(msg_json)
#     #     , get_msg_size(msg_json)
#     #     , decode_msg_size(get_msg_size(msg_json))
#     #     , msg_json)
#     socket.write(get_msg_size(msg_json))
#     socket.write(msg_json)
#
#
# def send_msg(msg_json, socket):
#     # print 'sending message {}.{}.{}.\'{}\''.format(
#     #     len(msg_json)
#     #     , get_msg_size(msg_json)
#     #     , decode_msg_size(get_msg_size(msg_json))
#     #     , msg_json)
#     socket.send(get_msg_size(msg_json))
#     socket.send(msg_json)

def make_msg(msg_type):
    return {'type': msg_type}

def make_session_msg(msg_type, cloudname, session_uuid):
    msg = make_msg(msg_type)
    msg['sid'] = session_uuid
    msg['cname'] = cloudname
    return msg


def decode_msg(msg):
    # print 'decoding\'{}\''.format(msg)
    obj = json.loads(msg)
    return obj

#
# def make_new_host_json(port):
#     msg = make_msg(NEW_HOST_MSG)
#     msg['port'] = port
#     return json.dumps(msg)
#
#
# def make_assign_host_id_json(host_id, key, cert):
#     msg = make_msg(ASSIGN_HOST_ID)
#     msg['id'] = host_id
#     msg['key'] = 'TODO placeholder key'
#     msg['cert'] = 'TODO placeholder cert'
#     return json.dumps(msg)
#
#
# def make_host_handshake_json(host_id, listening_port, last_update):
#     msg = make_msg(HOST_HANDSHAKE)
#     msg['id'] = host_id
#     msg['port'] = listening_port
#     msg['update'] = last_update
#     return json.dumps(msg)
#
#
# def make_request_cloud_json(host_id, cloudname, username, password):
#     msg = make_msg(REQUEST_CLOUD)
#     msg['id'] = host_id
#     msg['cname'] = cloudname
#     msg['uname'] = username
#     msg['pass'] = password
#     return json.dumps(msg)
#
#
# def make_prepare_for_fetch_json(host_id, cloudname, ip):
#     msg = make_msg(PREPARE_FOR_FETCH)
#     msg['id'] = host_id
#     msg['cname'] = cloudname
#     msg['ip'] = ip
#     return json.dumps(msg)
#
#
# def make_go_retrieve_here_json(host_id, ip, port):
#     msg = make_msg(GO_RETRIEVE_HERE)
#     msg['id'] = host_id  # todo maybe unneeded.
#     msg['ip'] = ip
#     msg['port'] = port
#     return json.dumps(msg)
#
#
# def make_host_host_fetch(host_id, cloudname, requested_root):
#     msg = make_msg(HOST_HOST_FETCH)
#     msg['id'] = host_id
#     msg['cname'] = cloudname
#     msg['root'] = requested_root
#     return json.dumps(msg)
#
#
# def make_host_file_transfer(host_id, cloudname, relative_pathname, is_dir, filesize):
#     msg = make_msg(HOST_FILE_TRANSFER)
#     msg['id'] = host_id
#     msg['cname'] = cloudname
#     msg['fpath'] = relative_pathname
#     msg['fsize'] = filesize
#     msg['isdir'] = is_dir
#     return json.dumps(msg)
#
#
# def make_mirroring_complete(host_id, cloudname):
#     msg = make_msg(MIRRORING_COMPLETE)
#     msg['id'] = host_id
#     msg['cname'] = cloudname
#     return json.dumps(msg)
#
#
# def make_get_hosts_request(host_id, cloudname):
#     msg = make_msg(GET_HOSTS_REQUEST)
#     msg['id'] = host_id
#     msg['cname'] = cloudname
#     # todo needs uniquely identifying info, so that not just anyone
#     # cont can get all the other hosts ip/ports
#     return json.dumps(msg)
#
#
# def make_get_hosts_response(cloud):
#     msg = make_msg(GET_HOSTS_RESPONSE)
#     msg['cname'] = cloud.name
#     hosts = cloud.hosts.all()
#     host_jsons = []
#     for host in hosts:
#         host_obj = {
#             'ip': host.ip
#             , 'port': host.port
#             , 'id': host.id
#             , 'update': host.last_update
#             , 'hndshk': host.last_handshake
#         }
#         host_jsons.append(host_obj)
#     msg['hosts'] = host_jsons
#     return json.dumps(msg)
#
#
# def make_remove_file(host_id, cloudname, updated_file):
#     msg = make_msg(REMOVE_FILE)
#     msg['id'] = host_id  # The id of the recipient
#     msg['cname'] = cloudname
#     msg['root'] = updated_file
#     return json.dumps(msg)
#
#
# def make_host_file_push(tgt_host_id, cloudname, updated_file):
#     msg = make_msg(HOST_FILE_PUSH)
#     msg['tid'] = tgt_host_id
#     msg['cname'] = cloudname
#     msg['fpath'] = updated_file
#     return json.dumps(msg)
#
#
# def make_client_session_request(cloudname, username, password):
#     msg = make_msg(CLIENT_SESSION_REQUEST)
#     msg['cname'] = cloudname
#     msg['uname'] = username
#     msg['pass'] = password
#     # msg['ip'] = ip  # this we will get from connection
#     return json.dumps(msg)
#
#
# def make_client_session_alert(cloudname, user_id, session_id, ip):
#     msg = make_session_msg(CLIENT_SESSION_ALERT, cloudname, session_id)
#     msg['uid'] = user_id
#     msg['ip'] = ip
#     return json.dumps(msg)
#
#
# def make_client_session_response(cloudname, session_id, nebs_ip, nebs_port):
#     msg = make_session_msg(CLIENT_SESSION_RESPONSE, cloudname, session_id)
#     msg['ip'] = nebs_ip
#     msg['port'] = nebs_port
#     return json.dumps(msg)
#
#
# def make_stat_dict(file_path):
#     """You should make sure file exists before calling this."""
#     if file_path is None:
#         return None
#     if not os.path.exists(file_path):
#         return None
#     file_path = os.path.normpath(file_path)
#     file_stat = os.stat(file_path)
#     stat_dict = {
#         'atime': file_stat.st_atime
#         , 'mtime': file_stat.st_mtime
#         , 'ctime': file_stat.st_ctime
#         , 'inode': file_stat.st_ino
#         , 'mode': file_stat.st_mode
#         , 'dev': file_stat.st_dev
#         , 'nlink': file_stat.st_nlink
#         , 'uid': file_stat.st_uid
#         , 'gid': file_stat.st_gid
#         , 'size': file_stat.st_size
#         , 'name': os.path.basename(file_path)
#     }
#     return stat_dict
#
#
# def make_stat_request(cloudname, session_id, rel_path):
#     msg = make_session_msg(STAT_FILE_REQUEST,cloudname, session_id)
#     msg['fpath'] = rel_path
#     return json.dumps(msg)
#
#
# def make_stat_response(cloudname, rel_path, file_path):
#     msg = make_msg(STAT_FILE_RESPONSE)
#     msg['cname'] = cloudname
#     msg['fpath'] = rel_path
#     msg['stat'] = make_stat_dict(file_path)
#     return json.dumps(msg)
#
#
# def make_ls_array(file_path):
#     """You should make sure file exists before calling this."""
#     if file_path is None:
#         return None
#     if not os.path.exists(file_path):
#         return None
#     file_path = os.path.normpath(file_path)
#     subdirs = []
#     if not os.path.isdir(file_path):
#         # fixme this should somehow indicate the path was not a dir
#         # cont not just that it had no children
#         return subdirs
#     subfiles_list = os.listdir(file_path)
#     # print subfiles_list
#     for f in subfiles_list:
#         subdirs.append(make_stat_dict(os.path.join(file_path, f)))
#     return subdirs
#
#
# def make_list_files_request(cloudname, session_id, rel_path):
#     msg = make_session_msg(LIST_FILES_REQUEST,cloudname, session_id)
#     msg['fpath'] = rel_path
#     return json.dumps(msg)
#
#
# def make_list_files_response(cloudname, rel_path, file_path):
#     msg = make_msg(LIST_FILES_RESPONSE)
#     msg['cname'] = cloudname
#     msg['fpath'] = rel_path
#     msg['stat'] = make_stat_dict(file_path)
#     msg['ls'] = make_ls_array(file_path)
#     return json.dumps(msg)
#
#
#
# def make_client_file_put(cloudname, session_id, updated_file):
#     msg = make_session_msg(CLIENT_FILE_PUT, cloudname, session_id)
#     # msg['tid'] = tgt_host_id  # note: won't know the host id, host
#     # cont proc will differentiate based on sid
#     msg['fpath'] = updated_file
#     return json.dumps(msg)
#
#
# def make_client_file_transfer(cloudname, session_id, relative_pathname, is_dir, filesize):
#     msg = make_session_msg(CLIENT_FILE_TRANSFER, cloudname, session_id)
#     # msg['id'] = host_id  # note: see above
#     msg['fpath'] = relative_pathname
#     msg['fsize'] = filesize
#     msg['isdir'] = is_dir
#     return json.dumps(msg)
