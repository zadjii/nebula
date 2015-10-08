import socket
from subprocess import Popen, call, PIPE
from host import REMOTE_HOST, REMOTE_PORT
from host.util import setup_remote_socket
from test.repop_dbs import repop_dbs

__author__ = 'Mike'

from datetime import datetime
from time import sleep
from msg_codes import *

def client_setup_test():
    print '#' * 80
    print '# testing setting up a client session'
    print '#' * 80

    remote_proc = Popen('python nebr.py start')
    # remote_proc = call('python nebr.py start')
    sleep(1)
    print 'remote pid: {}'.format(remote_proc.pid)
    sleep(1)
    host_proc = Popen('python nebs.py mirror --test -r localhost -d test_out/tmp0 qwer', stdin=PIPE)
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
    host_proc = Popen('python nebs.py start')
    # remote_proc = call('python nebr.py start')
    sleep(1)
    print 'host2 pid: {}'.format(host_proc.pid)
    # sleep(1)

    rem_sock = setup_remote_socket(REMOTE_HOST, REMOTE_PORT)
    print '__ setup remote socket __'
    request = make_client_session_request('qwer', 'asdf', 'asdf')

    send_msg(request, rem_sock)
    print '__ sent client session request message __'
    print '__ msg:{}__'.format(request)
    response = recv_msg(rem_sock)
    print '__ resp:{}__'.format(response)

    if not (response['type'] == CLIENT_SESSION_RESPONSE):
        raise Exception('remote did not respond with success')
    session_id = response['sid']
    tgt_host_ip = response['ip']
    tgt_host_port = response['port']

    host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_sock.connect((tgt_host_ip, tgt_host_port))
    print '__ setup host socket __'
    send_msg(
        make_list_files_request('qwer', session_id, '.')
        , host_sock
    )
    response = recv_msg(host_sock)
    print response
    if response['type'] != LIST_FILES_RESPONSE:
        print '__that\'s bad, mmkay?__'
        teardown(remote_proc, host_proc)
        return
    sleep(5)
    resp0 = response
    ls0 = resp0['ls']

    os.makedirs('test_out/tmp0/qwer')
    os.makedirs('test_out/tmp0/asdf')
    os.makedirs('test_out/tmp0/asdf/foo')
    os.makedirs('test_out/tmp0/zxcv')
    print '__ made some new dirs__'
    sleep(1)
    print '__ checking for new dirs__'
    # host_sock.close()  #todo this is dumb
    # cont we should be able to reuse the connection.
    # but there's a lot of ways that could go wrong... right?
    # host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # host_sock.connect((tgt_host_ip, tgt_host_port))

    send_msg(
        make_list_files_request('qwer', session_id, '.')
        , host_sock
    )
    response = recv_msg(host_sock)
    print response
    if response['type'] != LIST_FILES_RESPONSE:
        print '__that\'s bad, mmkay?__'
        teardown(remote_proc, host_proc)
        return
    resp1 = response
    ls1 = resp1['ls']
    print '__these should be different {}!={}__'.format(
        len(ls0), len(ls1)
    )

    sleep(5)
    teardown(remote_proc, host_proc)


def teardown(remote_proc, host_proc):
    remote_proc.kill()
    host_proc.kill()
    print '#' * 80
    print '# </CLIENT SETUP TEST>'
    print '#' * 80
    # print rem_out
    # sleep(1)

if __name__ == '__main__':
    repop_dbs()
    client_setup_test()
    # fixme make sure I kill all children before exiting

