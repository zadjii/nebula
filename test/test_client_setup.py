import os
import socket

from host import REMOTE_HOST, REMOTE_PORT

from host.util import setup_remote_socket
# from messages.ClientGetCloudHostRequest import ClientGetCloudHostRequest
# from messages.ClientGetCloudsRequest import ClientGetCloudsRequest
# from messages import *
from test.all_dbs_repop import repop_dbs
from test.util import start_nebs_and_nebr, teardown_children
from connections.RawConnection import RawConnection

__author__ = 'Mike'

from time import sleep
from msg_codes import *
from messages import *

remote_proc, host_proc = None, None


def verify_type_or_teardown(msg, type):
    if msg.type != type:
        print '__that\'s bad, mmkay?__'
        teardown()
        raise Exception()


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
    # send_msg(msg, host_sock)
    return conn


def client_setup_test():
    try:
        client_setup_test_actual()
    finally:
        pass
    teardown()


def client_setup_test_actual():

    print '#' * 80
    print '# testing setting up a client session'
    print '#' * 80
    global host_proc, remote_proc
    test_root = 'client_test'
    neb_1_path = os.path.join(test_root, 'tmp0')
    neb_2_path = os.path.join(test_root, 'tmp1')

    if not os.path.exists(test_root):
        os.makedirs(test_root)
    if not os.path.exists(neb_1_path):
        os.makedirs(neb_1_path)
    if not os.path.exists(neb_2_path):
        os.makedirs(neb_2_path)

    host_proc, host_1_proc, remote_proc = start_nebs_and_nebr(test_root)

    rem_sock = setup_remote_socket(REMOTE_HOST, REMOTE_PORT)
    rem_conn = RawConnection(rem_sock)
    print '__ setup remote socket __'
    # request = make_client_session_request('qwer', 'asdf', 'asdf')
    request = ClientSessionRequestMessage('asdf', 'asdf')
    # send_msg(request, rem_sock)
    rem_conn.send_obj(request)
    print '__ sent client session request message __'
    print '__ msg:{}__'.format(request.__dict__)
    # response = recv_msg(rem_sock)
    response = rem_conn.recv_obj()
    print '__ resp:{}__'.format(response.__dict__)

    if not (response.type == CLIENT_SESSION_RESPONSE):
        raise Exception('remote did not respond with success')

    session_id = response.sid

    ############
    rem_sock = setup_remote_socket(REMOTE_HOST, REMOTE_PORT)
    rem_conn = RawConnection(rem_sock)

    msg = ClientGetCloudsRequestMessage(session_id)
    rem_conn.send_obj(msg)
    resp = rem_conn.recv_obj()
    if not (resp.type == CLIENT_GET_CLOUDS_RESPONSE):
        raise Exception('remote did not respond with success CGCR')
    print resp.__dict__

    cloudname = resp.owned[0]

    ############
    rem_sock = setup_remote_socket(REMOTE_HOST, REMOTE_PORT)
    rem_conn = RawConnection(rem_sock)

    msg = ClientGetCloudHostRequestMessage(session_id, cloudname)
    rem_conn.send_obj(msg)
    resp = rem_conn.recv_obj()
    if not (resp.type == CLIENT_GET_CLOUD_HOST_RESPONSE):
        raise Exception('remote did not respond with success CGCR')
    print resp.__dict__

    tgt_host_ip = resp.ip
    tgt_host_port = resp.port

    ############
    print '__ setting up host socket __'
    msg = ListFilesRequestMessage(session_id, 'qwer', '.')
    response = create_sock_msg_get_response(
        tgt_host_ip
        , tgt_host_port
        , msg
    )

    print response
    verify_type_or_teardown(response, LIST_FILES_RESPONSE)

    resp0 = response
    ls0 = resp0.ls

    if not os.path.exists(neb_2_path):
        os.makedirs('test_out/tmp0/qwer')
    if not os.path.exists(neb_2_path):
        os.makedirs('test_out/tmp0/asdf')
        pass
    if not os.path.exists(neb_2_path):
        os.makedirs('test_out/tmp0/qwer')
        pass
    if not os.path.exists(neb_2_path):
        os.makedirs('test_out/tmp0/qwer')
        pass

    # fix all the paths to use actual constants and shit.
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

    # send_msg(
    #     make_list_files_request('qwer', session_id, '.')
    #     , host_sock
    # )
    # response = recv_msg(host_sock)

    print '__ setting up host socket __'
    msg = ListFilesRequestMessage(session_id, 'qwer', '.')

    response = create_sock_msg_get_response(
        tgt_host_ip
        , tgt_host_port
        , msg
    )
    print response
    verify_type_or_teardown(response, LIST_FILES_RESPONSE)

    resp1 = response
    ls1 = resp1.ls
    print '__these should be different {}!={}__'.format(
        len(ls0), len(ls1)
    )

    ls_path(session_id, tgt_host_ip, tgt_host_port, './')
    ls_path(session_id, tgt_host_ip, tgt_host_port, './asdf')
    ls_path(session_id, tgt_host_ip, tgt_host_port, './tmp0')

    sleep(5)
    teardown()


def ls_path(session_id, tgt_host_ip, tgt_host_port, path):
    print '__ setting up host socket for ls {}__'.format(path)
    msg = ListFilesRequestMessage(session_id, 'qwer', path)
    response = create_sock_msg_get_response(
        tgt_host_ip
        , tgt_host_port
        , msg
    )
    print '__ ls {} response=({})'.format(path, response.__dict__)
    verify_type_or_teardown(response, LIST_FILES_RESPONSE)
    print '__ {} ls contents=({})'.format(path, response.ls)


def teardown():
    teardown_children([remote_proc, host_proc])
    print '#' * 80
    print '# </CLIENT SETUP TEST>'
    print '#' * 80


if __name__ == '__main__':
    repop_dbs()
    client_setup_test()
    # fixme make sure I kill all children before exiting

