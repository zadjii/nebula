import json

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


def make_msg(msg_type):
    return {'type' : msg_type}


def decode_msg(msg):
    return json.loads(msg)

def make_new_host_json():
    msg = make_msg(NEW_HOST_MSG)
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

def make_mirroring_complete(host_id, cloudname):
    msg = make_msg(MIRRORING_COMPLETE)
    msg['id'] = host_id
    msg['cname'] = cloudname
    return json.dumps(msg)
