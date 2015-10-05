from subprocess import Popen, call
from host import REMOTE_HOST, REMOTE_PORT
from host.util import setup_remote_socket

__author__ = 'Mike'

from datetime import datetime
from time import sleep
from msg_codes import *

def client_setup():
    print '#' * 80
    print '# testing setting up a client session'
    print '# '
    print '# (You need a remote and mirrored host running for this to work)'
    print '#' * 80

    remote_proc = Popen('python nebr.py start')
    # remote_proc = call('python nebr.py start')
    sleep(1)
    print 'remote pid: {}'.format(remote_proc.pid)
    sleep(1)
    host_proc = Popen('python nebs.py mirror -r localhost -d c:\\tmp\\tmp2 qwer')
    print 'host1 pid: {}'.format(host_proc.pid)
    sleep(1)
    host_proc.wait()
    print '__ first host finished __'
    # host_proc.communicate('asdf\n')
    # host_proc.communicate('asdf\n')
    sleep(2)
    host_proc = Popen('python nebs.py start')
    # remote_proc = call('python nebr.py start')
    sleep(1)
    print 'host2 pid: {}'.format(host_proc.pid)
    sleep(1)

    rem_sock = setup_remote_socket(REMOTE_HOST, REMOTE_PORT)
    print '__ setup remote socket __'
    request = make_client_session_request('qwer', 'asdf', 'asdf')

    send_msg(request, rem_sock)
    print '__ sent client session request message __'
    print '__ msg:{}__'.format(request)
    response = recv_msg(rem_sock)
    print '__ resp:{}__'.format(response)
    sleep(5)

    # rem_out = remote_proc.stdout.readall()
    # remote_proc.kill()
    print '#' * 80
    print '# REMOTE OUT'
    print '#' * 80
    # print rem_out
    sleep(1)
    remote_proc.kill()
    host_proc.kill()