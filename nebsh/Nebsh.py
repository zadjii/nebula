import getpass
import socket
from sys import stdin
from host import REMOTE_PORT
from host.util import setup_remote_socket
from msg_codes import *

__author__ = 'Mike'


class NebshClient(object):
    def __init__(self, args):
        self.testing, self.rem_addr, self.rem_port, self.cname =\
            process_args(args)
        self.rem_sock = None
        self.host_sock = None
        self.username = None

        self.session_id = None
        self.tgt_host_ip = None
        self.tgt_host_port = None

        self.cwd = None
        self.exit_requested = False

    def main(self):

        if self.testing:
            print('please enter username for {}:'.format(self.cname))
            self.username = stdin.readline()[:-1]
            print('Enter the password for ' + self.cname + ':')
            password = stdin.readline()[:-1]  # todo this is yea, bad.
        else:
            self.username = raw_input('Enter the username for ' + self.cname + ':').lower()
            password = getpass.getpass('Enter the password for ' + self.cname + ':')

        self.rem_sock = setup_remote_socket(self.rem_addr, self.rem_port)
        request = make_client_session_request(self.cname, self.username, password)
        send_msg(request, self.rem_sock)
        response = recv_msg(self.rem_sock)
        # print '__ resp:{}__'.format(response)
        if not (response['type'] == CLIENT_SESSION_RESPONSE):
            raise Exception('remote did not respond with success')
        self.session_id = response['sid']
        self.tgt_host_ip = response['ip']
        self.tgt_host_port = response['port']
        self.main_loop()

    def main_loop(self):
        response = create_sock_msg_get_response(
            self.tgt_host_ip
            , self.tgt_host_port
            , make_list_files_request(self.cname, self.session_id, '.')
        )
        print response
        self.cwd = response['fpath']
        while not self.exit_requested:
            inline = raw_input(do_prompt(self.cname, self.cwd))
            # tokenize that shit
            inarray = inline.split(' ')  # todo any whitespace
            print inarray
            command = inarray[0]
            if command == 'exit':
                self.exit_requested = True
            elif command == 'ls':
                self.ls(inarray)

    def ls(self, argv):
        # print 'ls [{}]'.format(argv[1:])
        dir = argv[-1]
        # print dir
        if dir == 'ls':
            dir = '.'
        rel_path = os.path.join(self.cwd, dir)
        response = create_sock_msg_get_response(
            self.tgt_host_ip
            , self.tgt_host_port
            , make_list_files_request(self.cname, self.session_id, rel_path)
        )
        if response['type'] != LIST_FILES_RESPONSE:
            print 'Error during ls:{}'.format(response)
            return
        # print response
        if response is not None:
            for child in response['ls']:
                print child['name']

    def stat(self, argv):
        pass

    def cat(self, argv):
        pass

    def pwd(self, argv):
        pass
    
    def cd(self):
        pass

def create_sock_msg_get_response(ip, port, msg):
    sock = create_sock_and_send(ip, port, msg)
    response = recv_msg(sock)
    sock.close()
    return response


def create_sock_and_send(ip, port, msg):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    send_msg(msg, sock)
    return sock


def nebsh_usage():
    print 'usage: nebsh [--test][-r address][-p port]' + \
        '[cloudname]'
    print ''

def process_args(argv):
    host = None
    port = REMOTE_PORT
    cloudname = None
    test_enabled = False
    if len(argv) < 1:
        nebsh_usage()
        return
    # print 'mirror', argv
    while len(argv) > 0:
        arg = argv[0]
        args_left = len(argv)
        args_eaten = 0
        if arg == '-r':
            if args_left < 2:
                # throw some exception
                raise Exception('not enough args supplied to -r')
            host = argv[1]
            args_eaten = 2
        elif arg == '-p':
            if args_left < 2:
                # throw some exception
                raise Exception('not enough args supplied to -p')
            port = argv[1]
            args_eaten = 2
        elif arg == '--test':
            test_enabled = True
            args_eaten = 1
        else:
            cloudname = arg
            args_eaten = 1
        argv = argv[args_eaten:]
    # TODO: disallow relative paths. Absolute paths or bust.
    if cloudname is None:
        raise Exception('Must specify a cloud name to mirror')
    if host is None:
        raise Exception('Must specify a host to mirror from')
    # print 'attempting to get cloud named \'' + cloudname + '\' from',\
    #     'host at [',host,'] on port[',port,'], into root [',root,']'
    return (test_enabled, host, port, cloudname)



def main(argv):
    print 'Nebula shell, v0'
    nebsh = NebshClient(argv)
    nebsh.main()
    # testing, rem_addr, rem_port, cname = process_args(argv)
    # rem_sock = setup_remote_socket(rem_addr, rem_port)
    # # todo prompt for uname, pass
    #
    # if testing:
    #     print('please enter username for {}:'.format(cname))
    #     username = stdin.readline()[:-1]
    #     print('Enter the password for ' + cname + ':')
    #     password = stdin.readline()[:-1]  # todo this is yea, bad.
    # else:
    #     username = raw_input('Enter the username for ' + cname + ':').lower()
    #     # print('Enter the password for ' + cname + ':')
    #     password = getpass.getpass('Enter the password for ' + cname + ':')
    #
    # request = make_client_session_request(cname, username, password)
    # send_msg(request, rem_sock)
    # response = recv_msg(rem_sock)
    # print '__ resp:{}__'.format(response)
    # if not (response['type'] == CLIENT_SESSION_RESPONSE):
    #     raise Exception('remote did not respond with success')
    # session_id = response['sid']
    # tgt_host_ip = response['ip']
    # tgt_host_port = response['port']
    #
    # print '__ setting up host socket __'
    #
    # # todo move these to global awshelper utils
    # response = create_sock_msg_get_response(
    #     tgt_host_ip
    #     , tgt_host_port
    #     , make_list_files_request(cname, session_id, '.')
    # )
    # exit_requested = False
    # cwd = './'
    # while not exit_requested:
    #     inline = raw_input(do_prompt(cname, cwd))
    #     # todo tokenize that shit
    #     inarray = inline.split(' ')
    #     print inarray
    #     command = inarray[0]
    #     if command == 'exit':
    #         exit_requested = True
    #     elif command == 'ls':
    #         # print 'ls [{}]'.format(inline[3:])
    #         response = create_sock_msg_get_response(
    #             tgt_host_ip
    #             , tgt_host_port
    #             , make_list_files_request(cname, session_id, inarray[1])
    #         )
    #         # print response
    #         if response is not None:
    #             for child in response['ls']:
    #                 print child['name']

def do_prompt(cname, rel_path):
    return '{}:{}>'.format(cname, rel_path)

