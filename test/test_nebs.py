import os
import shutil
import socket
from subprocess import Popen, PIPE
from time import sleep
from inspect import currentframe, getframeinfo

import signal

from common_util import ResultAndData, enable_vt_support, Success, Error
from connections.RawConnection import RawConnection
from host import REMOTE_HOST, REMOTE_PORT
from host.util import setup_remote_socket
from messages import *
from msg_codes import *
from test.util import teardown_children, start_nebs_and_nebr
from test.all_dbs_repop import repop_dbs
from remote.tools.remote_autopop_001 import repop as wedding_repop

remote = None
host_0 = None
host_1 = None

test_root = 'basic_test'

neb_1_path = os.path.join(test_root, 'tmp0')
neb_2_path = os.path.join(test_root, 'tmp1')
wedding_0_root = os.path.join(test_root, 'wedding_0')
wedding_1_root = os.path.join(test_root, 'wedding_1')
wedding_2_root = os.path.join(test_root, 'wedding_2')

bridesmaids_0_root = os.path.join(test_root, 'bridesmaids_0')
bridesmaids_1_root = os.path.join(test_root, 'bridesmaids_1')

bachelorette_0_root = os.path.join(test_root, 'bachelorette_0')
bachelorette_1_root = os.path.join(test_root, 'bachelorette_1')

# DONT USE DIRECTLY
def _log_message(text, fmt):
    frameinfo = getframeinfo(currentframe().f_back.f_back)

    print('[{}:{}]\x1b[{}m{}\x1b[0m'.format(
        os.path.basename(frameinfo.filename)
        , frameinfo.lineno
        , fmt
        , text))


def log_success(text):
    _log_message(text, '32')

def log_fail(text):
    _log_message(text, '31')

def log_warn(text):
    _log_message(text, '33')

def log_text(text, fmt='0'):
    _log_message(text, fmt)

# def log_rd(rd, reverse=False):
#     if not reverse:
#         log_fail(rd.data) if not rd.success else log_success(rd.data)
#     else:
#         log_fail(rd.data) if rd.success else log_success(rd.data)

def close_env():
    global host_0, host_1, remote
    teardown_children([host_0, remote])
    sleep(2)


def setup_env():
    repop_dbs()
    wedding_repop()
    # Todo: replace repoping with test-driven population
    # reset_dbs()

    if os.path.exists(test_root):
        for root, dirs, files in os.walk(test_root, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    if os.path.exists(test_root):
        shutil.rmtree(test_root, ignore_errors=True)
    sleep(.5)
    os.makedirs(test_root)
    os.makedirs(neb_1_path)
    os.makedirs(neb_2_path)

    os.makedirs(wedding_0_root)
    os.makedirs(wedding_1_root)
    os.makedirs(wedding_2_root)

    os.makedirs(bridesmaids_0_root)
    os.makedirs(bridesmaids_1_root)

    os.makedirs(bachelorette_0_root)
    os.makedirs(bachelorette_1_root)

    log_warn('Made the test root:<{}>'.format(test_root))

    # os.environ.set('NEBULA_LOCAL_DEBUG', True)
    os.environ['NEBULA_LOCAL_DEBUG'] = '1'
    global host_0, host_1, remote
    try:
        host_0, host_1, remote = start_nebs_and_nebr(test_root)
        print '\x1b[30;42m##### Nebula processes started #####\x1b[0m'
    except Exception, e:
        teardown_children([host_0, remote])
        raise e

    # maybe here test client mirroring?



def basic_test():
    setup_env()
    enable_vt_support()
    try:
        test_file_push_simple()
        test_client_setup()
        test_client_io()
        test_client_mirror()
    finally:
        pass
    close_env()


def test_file_push_simple():
    filename = "foo.txt"

    neb_1_file = os.path.join(neb_1_path, filename)
    neb_2_file = os.path.join(neb_2_path, filename)

    # make a file on neb 0
    fd = open(neb_1_file, mode='wb')
    for i in range(0, 4 * 1024):
        fd.write('Line {}\n'.format(i))
    fd.close()
    # wait a sec
    sleep(3)

    # test it exists on neb 2
    file_exists = os.path.exists(neb_2_file)
    if file_exists:
        log_success('File was copied to the second host')
    else:
        log_fail('File did not appear on second host')


def test_client_mirror():
    log_text('### Client Mirroring Test ###', '7')
    log_text('#### These two users CAN mirror the AfterglowWedding2017 cloud ####')

    rd = retrieve_client_session('Mike-Griese', 'Mike Griese')
    if not rd.success:
        return
    mike = rd.data
    log_success('successfully created Mike client')

    rd = retrieve_client_session('Claire-Bovee', 'Claire Bovee')
    if not rd.success:
        return
    claire = rd.data
    log_success('successfully created Claire client')

    log_text('#### These two users CANNOT mirror the wedding cloud ####')

    rd = retrieve_client_session('Hannah-Bovee', 'Hannah Bovee')
    if not rd.success:
        return
    hannah = rd.data
    log_success('successfully created Hannah client')

    rd = retrieve_client_session('Alli-Anderson', 'Alli Anderson')
    if not rd.success:
        return
    alli = rd.data
    log_success('successfully created Alli client')

    log_text('#### Create some test data ####')
    wedding_test_text_0 = 'Hello Wedding World!'
    wedding_test_file_0 = 'hello.txt'
    handle = open(os.path.join(wedding_0_root, wedding_test_file_0), mode='wb')
    handle.write(wedding_test_text_0)
    handle.close()
    log_text('#### Created test data in wedding_0_root ####')

    log_text('#### client mirror the wedding cloud successfully ####')

    mike.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_0_root)
    rd = check_file_contents(wedding_0_root, wedding_test_file_0, wedding_test_text_0)
    if not rd.success:
        log_fail('Failed mirroring wedding 0')
        return
    else:
        log_success('Succeeded mirroring wedding 0')

    claire.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_1_root)
    rd = check_file_contents(wedding_1_root, wedding_test_file_0, wedding_test_text_0)
    if not rd.success:
        log_fail('Failed mirroring wedding 1')
        return
    else:
        log_success('Succeeded mirroring wedding 1')

    log_text('#### client mirror the wedding cloud unsuccessfully ####')
    hannah.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_2_root)
    rd = check_file_contents(wedding_2_root, wedding_test_file_0, wedding_test_text_0)
    if rd.success:
        log_fail('Unfortunately Hannah mirrored wedding 2')
    else:
        log_success('Hannah did not mirror wedding 2')
    alli.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_2_root)
    rd = check_file_contents(wedding_2_root, wedding_test_file_0,
                             wedding_test_text_0)
    if rd.success:
        log_fail('Unfortunately Alli mirrored wedding 2')
    else:
        log_success('Alli did not mirror wedding 2')


def check_file_contents(root, path, data):
    try:
        handle = open(os.path.join(root, path))
        contents = handle.read()
        handle.close()
        return ResultAndData(data == contents, 'Checking {} file contents'.format(path))
    except Exception, e:
        return Error(e)


def get_client_session(uname, password):
    try:
        rem_sock = setup_remote_socket(REMOTE_HOST, REMOTE_PORT)
        rem_conn = RawConnection(rem_sock)
        request = ClientSessionRequestMessage(uname, password)
        rem_conn.send_obj(request)
        response = rem_conn.recv_obj()
        if not (response.type == CLIENT_SESSION_RESPONSE):
            raise Exception('remote did not respond with success')
        return ResultAndData(True, response)
    except Exception, e:
        return ResultAndData(False, e)


def get_client_host(sid, cloud_uname, cname):
    try:
        rem_sock = setup_remote_socket(REMOTE_HOST, REMOTE_PORT)
        rem_conn = RawConnection(rem_sock)

        msg = ClientGetCloudHostRequestMessage(sid, cname)
        rem_conn.send_obj(msg)
        response = rem_conn.recv_obj()
        if not (response.type == CLIENT_GET_CLOUD_HOST_RESPONSE):
            raise Exception('remote did not respond with success CGCR')
        return ResultAndData(True, response)
    except Exception, e:
        return ResultAndData(False, e)


def create_sock_msg_get_response(ip, port, msg):
    conn = create_sock_and_send(ip, port, msg)
    response = conn.recv_obj()
    conn.close()
    return response


def create_sock_and_send(ip, port, msg):
    host_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    host_sock.connect((ip, port, 0, 0))
    conn = RawConnection(host_sock)
    conn.send_obj(msg)
    return conn

def test_client_setup():
    log_text('### Client Setup Test ###', '7')
    # Create a valid session
    rd = get_client_session('asdf', 'asdf')
    if not rd.success:
        log_fail('Failed to create session')
    else:
        log_success('Created good session')

    # Create an invalid session
    rd = get_client_session('asdf', 'invalid')
    if rd.success:
        log_fail('Created a session?')
    else:
        log_success('Didn\'t create a bad session')

    rd = get_client_session('invalid', 'invalid')
    if rd.success:
        log_fail('Created a session?')
    else:
        log_success('Didn\'t create a bad session')

    # Create a duplicate session
    rd = get_client_session('asdf', 'asdf')
    if not rd.success:
        log_fail('Failed to create duplicate session')
    else:
        log_success('Created good session')


def test_client_io():
    log_text('### Client IO Test ###', '7')

    session_0 = None

    # Create a valid session
    rd = get_client_session('asdf', 'asdf')
    if not rd.success:
        log_fail('Failed to create session')
        return
    else:
        log_success('Created good session')
        session_0 = HostSession(rd.data.sid)

    rd = session_0.get_host('asdf', 'qwer')
    # rd = get_client_host(sid_0, 'asdf', 'qwer')
    if not rd.success:
        log_fail('Failed to get host for session')
        return
    else:
        log_success('Got Host for session')
        host_0_ip = rd.data.ip
        host_0_port = rd.data.port

    log_text('#### Test ls on some files ####', '7')
    rd = session_0.ls('.')
    log_fail(rd.data.serialize()) if not rd.success else log_success(rd.data.serialize())

    rd = session_0.ls('foo.txt')
    log_fail(rd.data.serialize()) if not rd.success else log_success(rd.data.serialize())

    rd = session_0.ls('doesntexist.txt')
    log_fail(rd.data.serialize()) if not rd.success else log_success(rd.data.serialize())

    log_text('#### Create a file ####', '7')
    filename = 'bar.txt'
    rd = session_0.write(filename, 'bar'*80)
    neb_1_file = os.path.join(neb_1_path, filename)
    neb_2_file = os.path.join(neb_1_path, filename)
    sleep(2)

    log_text('##### Make sure it was copied #####', '7')
    # test it exists on neb 1
    file_exists = os.path.exists(neb_1_file)
    if file_exists:
        log_success('File was copied to the first host')
    else:
        log_fail('File did not appear on first host')

    # test it exists on neb 2
    file_exists = os.path.exists(neb_2_file)
    if file_exists:
        log_success('File was copied to the second host')
    else:
        log_fail('File did not appear on second host')

    log_text('##### Make sure it was copied CORRECTLY #####', '7')
    rd = session_0.read_file(filename)
    if rd.success:
        log_success('Reading file from client returned successfully')
        client_data = rd.data
        neb_1_handle = open(neb_1_file)
        n1_data = neb_1_handle.read()
        if client_data == n1_data:
            log_success('Neb 1 == client')
        else:
            log_fail('Neb 1 != client')
        neb_1_handle.close()

        neb_2_handle = open(neb_2_file)
        n2_data = neb_2_handle.read()
        if client_data == n2_data:
            log_success('Neb 2 == client')
        else:
            log_fail('Neb 2 != client')
        neb_2_handle.close()
    else:
        log_fail('Failed to read file with the client')
        return

    log_text('##### Modify the data #####', '7')
    client_data += 'baz'*20
    rd = session_0.write(filename, client_data)
    sleep(2)
    if rd.success:
        neb_1_handle = open(neb_1_file)
        n1_data = neb_1_handle.read()
        if client_data == n1_data:
            log_success('Neb 1 == client')
        else:
            log_fail('Neb 1 != client')
        neb_1_handle.close()

        neb_2_handle = open(neb_2_file)
        n2_data = neb_2_handle.read()
        if client_data == n2_data:
            log_success('Neb 2 == client')
        else:
            log_fail('Neb 2 != client')
        neb_2_handle.close()

def retrieve_client_session(uname, password):
    rd = get_client_session(uname, password)
    if not rd.success:
        log_fail('Failed to create session')
    else:
        log_success('Created good session')
        rd = Success(HostSession(rd.data.sid))
    return rd


class HostSession(object):
    def __init__(self, sid):
        self.sid = sid
        self.cloud_uname = None
        self.cname = None
        self.ip = None
        self.port = None

    def get_host(self, cloud_uname, cname):
        self.cloud_uname = cloud_uname
        self.cname = cname
        rd = get_client_host(self.sid, self.cloud_uname, self.cname)
        if rd.success:
            self.ip = rd.data.ip
            self.port = rd.data.port
        return rd

    def connect(self):
        host_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        host_sock.connect((self.ip, self.port, 0, 0))
        conn = RawConnection(host_sock)
        return conn

    def ls(self, path):
        msg = ListFilesRequestMessage(self.sid, self.cname, path)
        response = create_sock_msg_get_response(
            self.ip
            , self.port
            , msg
        )
        return ResultAndData(response.type == LIST_FILES_RESPONSE, response)

    def write(self, path, data):
        msg = ClientFilePutMessage(self.sid, self.cname, path)
        conn = create_sock_and_send(self.ip, self.port, msg)
        msg = ClientFileTransferMessage(self.sid, self.cname, path, len(data), False)
        conn.send_obj(msg)
        conn.send_next_data(data)
        return ResultAndData(True, 'Write doesnt check success LOL todo')

    def read_file(self, path):
        msg = ReadFileRequestMessage(self.sid, self.cname, path)
        conn = self.connect()
        conn.send_obj(msg)
        resp = conn.recv_obj()
        if resp.type == READ_FILE_RESPONSE:
            fsize = resp.fsize
            data = conn.recv_next_data(fsize)
            return Success(data)
        else:
            return Error(resp)

    def mirror(self, uname, cname, local_root):
        mirror_proc = Popen('python {} mirror -r {} -d {} -s {} {}'
                            .format('nebs.py'
                                    , 'localhost'
                                    , local_root
                                    , self.sid
                                    , cname))
        log_text('Created mirror process')
        mirror_proc.wait()
        log_text('mirror process joined')

