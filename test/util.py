import os
import socket
from inspect import currentframe
from inspect import getframeinfo
from subprocess import Popen, PIPE
from time import sleep

from common.Instance import Instance
from common_util import INSTANCES_ROOT, NEBULA_ROOT, Success, ResultAndData, Error
from connections.RawConnection import RawConnection
from host import REMOTE_HOST, REMOTE_PORT
from host.util import setup_remote_socket
from messages import *
from msg_codes import *
from messages import ListFilesRequestMessage, ClientFilePutMessage, ClientFileTransferMessage, ReadFileRequestMessage, \
    ClientAddOwnerMessage, ClientAddContributorMessage
from msg_codes import LIST_FILES_RESPONSE, READ_FILE_RESPONSE, ADD_OWNER_SUCCESS, ADD_CONTRIBUTOR_SUCCESS
from test.all_dbs_repop import repop_dbs
# from test.test_nebs import get_client_session, log_fail, log_success, get_client_host, create_sock_msg_get_response, \
#     create_sock_and_send, log_text

__author__ = 'Mike'


def start_nebs(host_dir, host_id, start_after_mirror):
    host_proc = Popen(
        'python nebs.py mirror --test -r localhost -d {} asdf/qwer'.format(host_dir)
        , stdin=PIPE
        , shell=True)
    print 'nebs[{}] mirror pid: {}'.format(host_id, host_proc.pid)
    sleep(1)
    host_proc.communicate('asdf\nasdf\n')  # enter username, password
    print '__ sent asdf asdf __'
    sleep(1)
    host_proc.wait()
    print '__ nebs mirror finished __'
    if start_after_mirror:
        sleep(2)
        print '\x1b[45m__ Creating first host __\x1b[0m'
        # host_proc = Popen('python nebs.py start', shell=True)
        host_proc = Popen('python nebs.py start')
        sleep(1)
        print 'nebs[{}] start pid: {}'.format(host_id, host_proc.pid)
        return host_proc
    return None


def start_nebs_and_nebr(root='test_out'):
    # remote_proc = Popen('python nebr.py start', shell=True)
    remote_proc = Popen('python nebr.py start')
    # remote_proc = call('python nebr.py start')
    sleep(1)
    print '----- remote pid: {}'.format(remote_proc.pid)
    sleep(1)
    host_proc_0 = start_nebs(os.path.join(root, 'tmp0'), 1, True)
    print '----- \x1b[45m__ first host created __\x1b[0m'
    print '----- Waitin` for Host 0 to finish setup.'
    sleep(2)
    print '----- We want to see a Mirroring Complete (14) before this.'
    print '----- (and make sure it\'s from host [1]'
    host_proc_1 = start_nebs(os.path.join(root, 'tmp1'), 2, False)
    print '\x1b[44m__ second host finished __\x1b[0m'
    return host_proc_0, host_proc_1, remote_proc


def start_nebr_and_nebs_instance(instance_name='test'):
    nebr_path = os.path.join(NEBULA_ROOT, './nebr.py')
    nebs_path = os.path.join(NEBULA_ROOT, './nebs.py')

    # remote_working_dir = os.path.join(INSTANCES_ROOT, './remote/{}'.format(instance_name))
    # host_working_dir = os.path.join(INSTANCES_ROOT, './host/{}'.format(instance_name))

    remote_working_dir, argv = Instance.get_working_dir(['-i', instance_name], is_remote=True)
    host_working_dir, argv = Instance.get_working_dir(['-i', instance_name], is_remote=False)

    remote_working_dir = os.path.join(NEBULA_ROOT, remote_working_dir)
    host_working_dir = os.path.join(NEBULA_ROOT, host_working_dir)

    log_text('remote, host WD\'s = {}, {}'.format(remote_working_dir, host_working_dir))
    # mirror_directory_0 = os.path.join(host_working_dir, './{}'.format(mirror_dir0))
    # mirror_directory_1 = os.path.join(host_working_dir, './{}'.format(mirror_dir1))

    remote_proc = Popen('python {} -w {} start'.format(nebr_path, remote_working_dir))
    sleep(.5)
    host_proc = Popen('python {} -w {} start'.format(nebs_path, host_working_dir))
    sleep(1.0)
    # remote_proc = Popen('python -w {} nebr.py start'.format(working_dir))
    # remote_proc = call('python nebr.py start')


    print '----- remote pid: {}'.format(remote_proc.pid)
    print 'nebs start pid: {}'.format(host_proc.pid)

    return remote_proc, host_proc
    #
    # sleep(1)
    # host_proc_0 = start_nebs(os.path.join(root, 'tmp0'), 1, True)
    # print '----- \x1b[45m__ first host created __\x1b[0m'
    # print '----- Waitin` for Host 0 to finish setup.'
    # sleep(2)
    # print '----- We want to see a Mirroring Complete (14) before this.'
    # print '----- (and make sure it\'s from host [1]'
    # host_proc_1 = start_nebs(os.path.join(root, 'tmp1'), 2, False)
    # print '\x1b[44m__ second host finished __\x1b[0m'
    # return host_proc_0, host_proc_1, remote_proc


def teardown_children(children):
    for child in children:
        if child is not None:
            child.kill()

    # print rem_out
    # sleep(1)

def populate_test_filesystem():
    print '#' * 80
    print '# populating some dirs'
    os.makedirs('test_out/tmp0/qwer')
    os.makedirs('test_out/tmp0/asdf')
    os.makedirs('test_out/tmp0/asdf/foo')
    os.makedirs('test_out/tmp0/zxcv')
    fd = open('test_out/tmp0/asdf/helloworld_root.txt', mode='wb')
    fd.write('Hello nebula!')
    fd.close()
    fd = open('test_out/tmp0/asdf/AHAHAHA.txt', mode='wb')
    fd.write('WAHAHAHAHA')
    fd.close()
    fd = open('test_out/tmp0/asdf/foo/helloworld.txt', mode='wb')
    fd.write('Hello nebula!\nThis is in ./asdf/foo/helloworld.txt')
    fd.close()
    fd = open('test_out/tmp0/asdf/foo/bar', mode='wb')
    fd.write('foobar'*100)
    fd.close()


def make_fresh_test_env():
    repop_dbs()
    if not os.path.exists('test_out/tmp0'):
        os.makedirs('test_out/tmp0')
        populate_test_filesystem()
    host_0, host_1, remote = None, None, None
    try:
        host_0, host_1, remote = start_nebs_and_nebr()
        # host_0 = hosts[0]
        # host_1 = hosts[1]
        print '\x1b[30;42m##### READY TO GO #####\x1b[0m'
        host_0.wait()
        # host_1.wait() # host 1 actually probably died a while ago, it just
        # mirrors then stops
        remote.wait()
    except Exception, e:
        teardown_children([host_0, host_1, remote])
        raise e


def get_client_host(sid, cloud_uname, cname):
    try:
        rem_sock = setup_remote_socket(REMOTE_HOST, REMOTE_PORT)
        rem_conn = RawConnection(rem_sock)

        msg = ClientGetCloudHostRequestMessage(sid, cloud_uname, cname)
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
        msg = ListFilesRequestMessage(self.sid, self.cloud_uname, self.cname, path)
        response = create_sock_msg_get_response(
            self.ip
            , self.port
            , msg
        )
        return ResultAndData(response.type == LIST_FILES_RESPONSE, response)

    def write(self, path, data):
        msg = ClientFilePutMessage(self.sid, self.cloud_uname, self.cname, path)
        conn = create_sock_and_send(self.ip, self.port, msg)
        msg = ClientFileTransferMessage(self.sid, self.cloud_uname, self.cname, path, len(data), False)
        conn.send_obj(msg)
        conn.send_next_data(data)
        conn.send_obj(ClientFileTransferMessage(self.sid, self.cloud_uname, self.cname, None, None, None))
        return ResultAndData(True, 'Write doesnt check success LOL todo')

    def mkdir(self, path):
        log_text('making directory for {}/{}, {}'.format(self.cloud_uname, self.cname, path))
        msg = ClientFilePutMessage(self.sid, self.cloud_uname, self.cname, path)
        conn = create_sock_and_send(self.ip, self.port, msg)
        msg = ClientFileTransferMessage(self.sid, self.cloud_uname, self.cname, path, 0, True)
        conn.send_obj(msg)
        conn.send_obj(ClientFileTransferMessage(self.sid, self.cloud_uname, self.cname, None, None, None))
        log_text('Sent CFT message')
        return ResultAndData(True, 'Write doesnt check success LOL todo')

    def read_file(self, path):
        msg = ReadFileRequestMessage(self.sid, self.cloud_uname, self.cname, path)
        conn = self.connect()
        conn.send_obj(msg)
        data_buffer = ''
        resp = conn.recv_obj()
        if resp.type == READ_FILE_RESPONSE:
            fsize = resp.fsize
            recieved = 0
            while recieved < fsize:
                data = conn.recv_next_data(fsize)
                # log_text('Read "{}"'.format(data))
                if len(data) == 0:
                    break
                recieved += len(data)
                data_buffer += data
            return Success(data_buffer)
        else:
            return Error(resp)

    def add_owner(self, new_owner_id):
        msg = ClientAddOwnerMessage(self.sid, new_owner_id, self.cloud_uname, self.cname)
        conn = self.connect()
        conn.send_obj(msg)
        resp = conn.recv_obj()
        if resp.type == ADD_OWNER_SUCCESS:
            return Success()
        else:
            return Error(resp)

    def share(self, new_owner_id, path, permissions):
        msg = ClientAddContributorMessage(self.sid, new_owner_id,
                                          self.cloud_uname, self.cname,
                                          path, permissions)
        conn = self.connect()
        conn.send_obj(msg)
        resp = conn.recv_obj()
        if resp.type == ADD_CONTRIBUTOR_SUCCESS:
            return Success()
        else:
            return Error(resp)

    def mirror(self, uname, cname, local_root, instance_root=None):
        log_text('Mirroring {}/{} into {}'.format(uname, cname, local_root))
        instance_command = ''
        if instance_root is not None:
            instance_command = '-w {}'.format(instance_root)
        command = 'python {} {} mirror -r {} -d {} -s {} {}/{}'.format(
            os.path.join(NEBULA_ROOT, 'nebs.py')
            , instance_command
            , 'localhost'
            , local_root
            , self.sid
            , uname
            , cname)
        log_text('Command is `{}`'.format(command))
        mirror_proc = Popen(command)
        log_text('Created mirror process')
        mirror_proc.wait()
        log_text('mirror process joined')


def check_file_contents(root, path, data):
    try:
        handle = open(os.path.join(root, path))
        contents = handle.read()
        handle.close()
        return ResultAndData(data == contents, 'Checking {} file contents'.format(path))
    except Exception, e:
        return Error(e)



###############################################################################
# Logging Pieces
###############################################################################
num_successes = 0
num_fails = 0
fail_messages = []

# DONT USE DIRECTLY
def _log_message(text, fmt):
    frameinfo = getframeinfo(currentframe().f_back.f_back)
    output = '[{}:{}]\x1b[{}m{}\x1b[0m'.format(
        os.path.basename(frameinfo.filename)
        , frameinfo.lineno
        , fmt
        , text)
    print(output)
    return output


def log_success(text):
    _log_message(text, '32')
    global num_successes
    num_successes += 1

def log_fail(text):
    output = _log_message(text, '31')
    global num_fails, fail_messages
    num_fails += 1
    fail_messages.append(output)

def log_warn(text):
    _log_message(text, '33')

def log_text(text, fmt='0'):
    _log_message(text, fmt)

