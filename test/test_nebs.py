import os
import shutil
from subprocess import Popen, PIPE
from time import sleep

import signal

from test.util import teardown_children, start_nebs_and_nebr
from test.all_dbs_repop import repop_dbs

remote = None
host_0 = None
host_1 = None

test_root = 'basic_test'

neb_1_path = os.path.join(test_root, 'tmp0')
neb_2_path = os.path.join(test_root, 'tmp1')


def log_success(text):
    print '\x1b[32m{}\x1b[0m'.format(text)
def log_fail(text):
    print '\x1b[31m{}\x1b[0m'.format(text)
def log_warn(text):
    print '\x1b[33m{}\x1b[0m'.format(text)

# def start_nebs(host_dir, host_id, start_after_mirror):
#     host_proc = Popen(
#         'python nebs.py mirror --test -r localhost -d {} qwer'.format(host_dir)
#         , stdin=PIPE
#         , shell=True)
#     print 'nebs[{}] mirror pid: {}'.format(host_id, host_proc.pid)
#     sleep(1)
#     host_proc.communicate('asdf\nasdf\n')  # enter username, password
#     print '__ sent asdf asdf __'
#     sleep(1)
#     host_proc.wait()
#     print '__ nebs mirror finished __'
#     if start_after_mirror:
#         sleep(2)
#         print '\x1b[45m__ Creating first host __\x1b[0m'
#         host_proc = Popen('python nebs.py start', shell=True)
#         sleep(1)
#         print 'nebs[{}] start pid: {}'.format(host_id, host_proc.pid)
#         return host_proc
#     return None


def close_env():
    global host_0,host_1, remote
    print host_0, host_1, remote
    teardown_children([host_0, host_1, remote])
    # os.setpgid()
    # os.killpg(os.getpgid(host_0.pid), signal.SIGTERM)
    # os.killpg(os.getpgid(remote.pid), signal.SIGTERM)
    sleep(2)
    shutil.rmtree(test_root)


def setup_env():
    repop_dbs()

    if not os.path.exists(test_root):
        os.makedirs(test_root)
    if not os.path.exists(neb_1_path):
        os.makedirs(neb_1_path)
    if not os.path.exists(neb_2_path):
        os.makedirs(neb_2_path)

    log_warn('Made the test root:<{}>'.format(test_root))
    global host_0, host_1, remote
    try:
        host_0, host_1, remote = start_nebs_and_nebr(test_root)
        print '\x1b[30;42m##### Nebula processes started #####\x1b[0m'
    except Exception, e:
        teardown_children([host_0, remote])
        raise e


def basic_test():
    setup_env()
    try:
        test_file_push_simple()
    finally:
        pass
    close_env()


def test_file_push_simple():
    filename = "foo.txt"

    neb_1_file = os.path.join(neb_1_path, filename)
    neb_2_file = os.path.join(neb_2_path, filename)

    if os.path.exists(neb_1_file):
        shutil.rmtree(neb_1_file)
    if os.path.exists(neb_2_file):
        shutil.rmtree(neb_2_file)

    # make a file on neb 0
    fd = open(neb_1_file, mode='wb')
    for i in range(0, 4 * 1024):
        fd.write('Line {}\n'.format(i))
    fd.close()
    # wait a sec
    sleep(1)

    # test it exists on neb 2
    file_exists = os.path.exists(neb_2_file)
    if file_exists:
        log_success('File was copied to the second host')
    else:
        log_fail('File did not appear on second host')
