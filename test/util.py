from subprocess import Popen, PIPE
from time import sleep
from test.repop_dbs import repop_dbs

__author__ = 'Mike'


def start_nebs_and_nebr():
    remote_proc = Popen('python nebr.py start', shell=True)
    # remote_proc = call('python nebr.py start')
    sleep(1)
    print 'remote pid: {}'.format(remote_proc.pid)
    sleep(1)
    host_proc = Popen(
        'python nebs.py mirror --test -r localhost -d test_out/tmp0 qwer',
        stdin=PIPE, shell=True)
    print 'host1 pid: {}'.format(host_proc.pid)
    sleep(1)
    host_proc.communicate('asdf\nasdf\n')
    # sleep(1)
    # host_proc.communicate('asdf')
    sleep(1)
    print '__ sent asdf asdf __'
    host_proc.wait()
    print '__ first host finished __'
    sleep(2)
    host_proc = Popen('python nebs.py start', shell=True)
    # remote_proc = call('python nebr.py start')
    sleep(1)
    print 'host2 pid: {}'.format(host_proc.pid)
    # sleep(1)
    return host_proc, remote_proc


def teardown_children(children):
    for child in children:
        if child is not None:
            child.kill()

    # print rem_out
    # sleep(1)


def make_fresh_test_env():
    repop_dbs()
    host, remote = None, None
    try:
        host, remote = start_nebs_and_nebr()
        host.wait()
        remote.wait()
    except Exception, e:
        teardown_children([host, remote])
        raise e


