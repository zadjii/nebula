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
from host.PrivateData import RDWR_ACCESS, READ_ACCESS, SHARE_ACCESS
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
        test_file_delete()
        test_client_setup()
        test_client_io()
        # test_client_io_big()  # This test is annoying.
        test_client_mirror()
        # test_client_mirror calls test_contributors
    finally:
        pass
    # let it settle down before wrapping up.
    sleep(5)

    # print summary of tests
    global num_fails, num_successes
    total_logs = num_fails + num_successes
    log_text('-'*80, '31' if num_fails > 0 else '32')
    log_text('')
    if num_fails > 0:
        log_text('Tests finished running with errors', '31')
    else:
        log_text('Tests finished running with no errors!', '32')
    log_text('')
    log_text('{}/{} successful logged messages'.format(num_successes, total_logs), '32')
    log_text('{}/{} logged error messages'.format(num_fails, total_logs), '31')
    if num_fails > 0:
        global fail_messages
        for msg in fail_messages:
            log_text('\t{}'.format(msg))
    log_text('')
    log_text('-'*80, '31' if num_fails > 0 else '32')

    close_env()


def test_file_push_simple():
    filename = "foo.txt"

    # neb_1_file = os.path.join(neb_1_path, 'dir')
    # neb_2_file = os.path.join(neb_2_path, 'dir')

    neb_1_file = os.path.join(neb_1_path, filename)
    neb_2_file = os.path.join(neb_1_path, filename)

    # make a file on neb 0
    fd = open(neb_1_file, mode='wb')
    for i in range(0, 4 * 1024):
        fd.write('Line {}\n'.format(i))
    fd.close()
    # wait a sec
    sleep(2)

    # test it exists on neb 2
    file_exists = os.path.exists(neb_2_file)
    if file_exists:
        log_success('File was copied to the second host')
    else:
        log_fail('File did not appear on second host')
        return

    # os.remove(neb_1_file)
    # sleep(1)
    # if file_exists:
    #     log_fail('File did not disappear on second host')
    #     return
    # else:
    #     log_success('File was deleted on the second host')



def test_file_delete():
    filename = "delete.txt"

    neb_1_file = os.path.join(neb_1_path, filename)
    neb_2_file = os.path.join(neb_2_path, filename)

    # make a file on neb 0
    fd = open(neb_1_file, mode='wb')
    for i in range(0, 4 * 1024):
        fd.write('Line {}\n'.format(i))
    fd.close()
    # wait a sec
    sleep(2)

    # test it exists on neb 2
    file_exists = os.path.exists(neb_2_file)
    if file_exists:
        log_success('File was copied to the second host')
    else:
        log_fail('File did not appear on second host')
        return

    os.remove(neb_1_file)
    sleep(1)
    file_exists = os.path.exists(neb_2_file)
    if file_exists:
        log_fail('File did not disappear on second host')
        return
    else:
        log_success('File was deleted on the second host')

    log_text('Make a dir, with children, then delete dir')
    dirname = 'delete-dir'
    barname = 'bar.txt'
    neb_1_dir = os.path.join(neb_1_path, dirname)
    neb_2_dir = os.path.join(neb_2_path, dirname)
    neb_1_bar = os.path.join(neb_1_dir, barname)
    neb_2_bar = os.path.join(neb_2_dir, barname)
    os.mkdir(neb_1_dir)
    fd = open(neb_1_bar, mode='wb')
    for i in range(0, 4 * 1024):
        fd.write('Line {}\n'.format(i))
    fd.close()

    # wait a sec
    sleep(1)
    # test it exists on neb 2
    file_exists = os.path.exists(neb_2_bar)
    if file_exists:
        log_success('File was copied to the second host')
    else:
        log_fail('File did not appear on second host')
        return

    shutil.rmtree(neb_1_dir)
    # wait a sec
    sleep(1)
    # test it exists on neb 2
    file_exists = os.path.exists(neb_2_bar)
    if file_exists:
        log_fail('File did not disappear on second host')
        return
    else:
        log_success('File was deleted on the second host')



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

    log_text('#### client mirror the wedding cloud successfully ####')

    mike.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_0_root)

    wedding_test_text_0 = 'Hello Wedding World!'
    wedding_test_file_0 = 'hello.txt'
    handle = open(os.path.join(wedding_0_root, wedding_test_file_0), mode='wb')
    handle.write(wedding_test_text_0)
    handle.close()
    log_text('#### Created test data in wedding_0_root ####')

    rd = check_file_contents(wedding_0_root, wedding_test_file_0, wedding_test_text_0)
    if not rd.success:
        log_fail('Failed mirroring wedding 0')
        return
    else:
        log_success('Succeeded mirroring wedding 0')

    claire.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_1_root)
    sleep(2)
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

    log_text('#### mirror the rest of the clouds ####')

    claire.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_2_root)
    sleep(2)
    rd = check_file_contents(wedding_2_root, wedding_test_file_0, wedding_test_text_0)
    if not rd.success:
        log_fail('Failed mirroring wedding 2')
        return
    else:
        log_success('Succeeded mirroring wedding 2')

    claire.mirror('Claire-Bovee', 'Claires-Bridesmaids', bridesmaids_0_root)
    handle = open(os.path.join(bridesmaids_0_root, wedding_test_file_0), mode='wb')
    handle.write(wedding_test_text_0)
    handle.close()
    log_text('#### Created test data in bridesmaids_0_root ####')
    handle = open(os.path.join(bachelorette_1_root, wedding_test_file_0), mode='wb')
    handle.write(wedding_test_text_0)
    handle.close()
    log_text('#### Created test data in bachelorette_1_root ####')
    sleep(2)

    log_text('#### Add an owner to the cloud and try mirroring with them ####')
    claire_clone = HostSession(claire.sid)
    rd = claire_clone.get_host('Claire-Bovee', 'Claires-Bridesmaids')
    if not rd.success:
        log_fail('failed to get_host')
        return
    # todo: actually get hannah's ID from the nebr. But for now we know it's [6]
    rd = claire_clone.add_owner(6)
    if not rd.success:
        log_fail('failed to add_owner')
        return

    hannah.mirror('Claire-Bovee', 'Claires-Bridesmaids', bridesmaids_1_root)
    sleep(1)
    rd = check_file_contents(bridesmaids_1_root, wedding_test_file_0, wedding_test_text_0)
    if not rd.success:
        log_fail('Failed mirroring bridesmaids 1')
        return
    else:
        log_success('Succeeded mirroring bridesmaids 1')

    log_text('#### Mirror a cloud, then mirror into a dir that already has a file ####')
    hannah.mirror('Hannah-Bovee', 'Claires_Bachelorette_Party', bachelorette_0_root)
    sleep(2)
    alli.mirror('Hannah-Bovee', 'Claires_Bachelorette_Party', bachelorette_1_root)
    rd = check_file_contents(bachelorette_1_root, wedding_test_file_0, wedding_test_text_0)
    if not rd.success:
        log_fail('Failed mirroring bachelorette 1 (This failure is expected)')
        # This is because the new process doesn't see that the file changed.
        #   It was already there. Mirror needs to be updated to account for this
        # todo:25
        # return
    else:
        log_success('Succeeded mirroring bachelorette 1')
    sleep(1)
    rd = check_file_contents(bachelorette_0_root, wedding_test_file_0, wedding_test_text_0)
    if not rd.success:
        log_fail('Failed mirroring bachelorette 0 (This failure is expected)')
        # This is because the new process doesn't see that the file changed.
        #   It was already there. Mirror needs to be updated to account for this
        # todo:25
        # return
    else:
        log_success('Succeeded mirroring bachelorette 0')

    sleep(3)  # let everything settle
    test_contributors()


def test_contributors():
    log_text('### Contributors Test ###', '7')
    log_text('#### This tests adding contributors, and testing their permissions ####')

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

    rd = retrieve_client_session('Mr-Bovee', 'Mr Bovee')
    if not rd.success:
        return
    mr_b = rd.data
    log_success('successfully created mr_b client')

    rd = mike.get_host('Mike-Griese', 'AfterglowWedding2017')
    if not rd.success:
        log_fail('')
        return
    claire_afterglow = HostSession(claire.sid)
    rd = claire_afterglow.get_host('Mike-Griese', 'AfterglowWedding2017')
    if not rd.success:
        log_fail('')
        return
    claire_bridesmaids = HostSession(claire.sid)
    rd = claire_bridesmaids.get_host('Claire-Bovee', 'Claires-Bridesmaids')
    if not rd.success:
        log_fail('')
        return
    log_success('Got hosts for mike, claire_afterglow, claire_bridesmaids')
    mike.mkdir('wedding')
    sleep(1)

    wedding_dir = os.path.join(wedding_0_root, './wedding')
    # wedding dir was made in one of the 3 hosts
    if not (os.path.exists(os.path.join(wedding_0_root, './wedding'))
            or os.path.exists(os.path.join(wedding_1_root, './wedding'))
            or os.path.exists(os.path.join(wedding_2_root, './wedding'))):
        log_fail('wedding directory doesnt exist, {}'.format(wedding_dir))

    wedding_readme_text = 'This is the wedding files directory'
    drafts_readme_text = 'This is where I\'ll prepare wedding docs'
    # write a file to the created dir
    mike.write('wedding/README.md', wedding_readme_text)
    # write a file to a dir that doesnt exist
    mike.write('drafts/README.md', drafts_readme_text)
    sleep(1)

    rd = mr_b.get_host('Mike-Griese', 'AfterglowWedding2017')
    if rd.success:
        log_fail('Mr B got host before he had access')
        # todo: this is something to be looked at, ability to get host for a
        #       client without being a owner/contributor
    else:
        log_success('Mr B did not get host')

    # mr_b has:
    #   /drafts: READ
    #   /finances: RDWR & Share

    # todo: actually get his ID, but we know it's [7] for now
    rd = mike.share(7, 'drafts', READ_ACCESS)
    if not rd.success:
        log_fail('failed to share drafts with mr_b')
        return

    rd = mr_b.get_host('Mike-Griese', 'AfterglowWedding2017')
    if rd.success:
        log_success('Mr B got host')
    else:
        log_fail('Mr B did not get host')
        return

    rd = mr_b.read_file('drafts/README.md')
    if not rd.success:
        log_fail('Mr B failed to read drafts/readme.md')
    else:
        if rd.data == drafts_readme_text:
            log_success('Mr B read drafts/readme.md correctly')
        else:
            log_fail('Mr B read drafts/readme.md incorrectly')

    # read file that doesn't exist
    rd = mr_b.read_file('finances/README.md')
    if not rd.success:
        log_success('Mr B failed to read finances/README.md, it doesnt exist')
    else:
        log_fail('Mr B was not rejected in reading finances/README.txt')

    mr_b_text = 'I\'m Mr Bovee writing nonsense\n'*1024
    log_text('#### Contributor DOESNT write to file they cant write to ####', '7')
    rd = mr_b.write('wedding/garbage.txt', mr_b_text)
    if rd.success:
        log_fail('Mr B wrote to wedding/garbage.txt, (This failure is expected)')
    else:
        log_success('Mr B failed to write to wedding/garbage.txt')

    rd = mike.share(7, 'finances', RDWR_ACCESS)
    if not rd.success:
        log_fail('failed to share finances with mr_b')

    log_text('#### Contributor writes to file they can write to ####', '7')
    rd = mr_b.write('finances/garbage.txt', mr_b_text)
    if rd.success:
        log_success('Mr B Wrote to finances/garbage.txt')
    else:
        log_fail('Mr B Failed to write to finances/garbage.txt')

    rd = mike.read_file('finances/garbage.txt')
    # it's possible Mike has a different host than Mr B
    if not rd.success:
        log_fail('Mike failed to read finances/garbage.txt')
    else:
        if rd.data == mr_b_text:
            log_success('Mike read finances/garbage.txt correctly')
        else:
            log_fail('Mike read finances/garbage.txt incorrectly,'
                     ' \nRead:"{}"\nExpected:"{}"'.format(len(rd.data), len(mr_b_text)))

    rd = mr_b.share(6, 'finances', RDWR_ACCESS)
    if not rd.success:
        log_success('failed to share finances with hannah')
    else:
        log_fail('mr_b shared finances even though he doesnt have share permission')


    # take away permission, but add a new one
    rd = mike.share(7, 'finances', SHARE_ACCESS)

    rd = mr_b.read_file('finances/garbage.txt')
    if not rd.success:
        log_success('Mr B failed to read finances/garbage.txt, no longer has permissions')
    else:
        log_fail('Mr B was not rejected in reading finances/garbage.txt')

    rd = mr_b.share(6, 'finances', RDWR_ACCESS)
    if not rd.success:
        log_success('failed to share finances with hannah, he doesnt have RDWR perm')
    else:
        log_fail('mr_b shared finances even though he doesnt have share permission')

    rd = mike.share(7, 'finances', RDWR_ACCESS | SHARE_ACCESS)
    rd = mr_b.read_file('finances/garbage.txt')
    if not rd.success:
        log_fail('Mr B failed to read finances/garbage.txt, no longer has permissions')
    else:
        log_success('Mr B was not rejected in reading finances/garbage.txt')

    rd = mr_b.share(6, 'finances', RDWR_ACCESS)
    if not rd.success:
        log_fail('failed to share finances with hannah, he should be able to')
    else:
        log_success('mr_b shared finances ')



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


def test_client_io_big():
    log_text('### Client IO Test on a BIG File###', '7')

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
    fail_count = 0
    for i in range(0, 15):
        log_text('#### Create a file ####', '7')
        filename = 'bar_{}.txt'.format(i)
        real_path = os.path.join(neb_1_path, filename)
        f = open(real_path, mode='wb')

        write_data = '0123456789ABCDE\n' * 1024  # * (2 ** i)
        for j in range(0, 2**i):
            f.write(write_data)
        log_text('wrote data {}'.format(i))
        sleep(3)

        rd = session_0.read_file(filename)
        if rd.success:  # and rd.data == write_data:
            # This can't use the write data to verify anymore. because the read data is write_data*2**i
            log_success('Read big data for {}'.format(i))
        else:
            log_fail('Read Failed for big data #{}'.format(i))
            fail_count += 1
            if fail_count > 3:
                return
            # log_text('Expected:\n{}'.format(write_data))
            # log_text('Received:\n{}'.format(rd.data))



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
        msg = ClientFilePutMessage(self.sid, self.cloud_uname, self.cname, path)
        conn = create_sock_and_send(self.ip, self.port, msg)
        msg = ClientFileTransferMessage(self.sid, self.cloud_uname, self.cname, path, 0, True)
        conn.send_obj(msg)
        conn.send_obj(ClientFileTransferMessage(self.sid, self.cloud_uname, self.cname, None, None, None))
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

    def mirror(self, uname, cname, local_root):
        mirror_proc = Popen('python {} mirror -r {} -d {} -s {} {}/{}'
                            .format('nebs.py'
                                    , 'localhost'
                                    , local_root
                                    , self.sid
                                    , uname
                                    , cname))
        log_text('Created mirror process')
        mirror_proc.wait()
        log_text('mirror process joined')

