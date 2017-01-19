import os
from subprocess import Popen, PIPE
from time import sleep
from test.all_dbs_repop import repop_dbs

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


