import getpass
import socket
from sys import stdin
from host import REMOTE_PORT
from host.util import setup_remote_socket
from msg_codes import *
from nebsh import mylog

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
        self.subdir_cache = None

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
        mylog.log_dbg(response)
        self.cwd = response['fpath']
        self.subdir_cache = response['ls']
        while not self.exit_requested:
            inline = raw_input(do_prompt(self.cname, self.cwd))
            # tokenize that shit
            inarray = inline.split(' ')  # todo any whitespace
            mylog.log_dbg(inarray)
            command = inarray[0]
            if command == 'exit':
                self.exit_requested = True
            if '--local' in inarray or '-\\l' in inarray:
                self.local_command(command, inarray)
            elif command == 'ls':
                self.ls(inarray)
            elif command == 'cd':
                self.cd(inarray)
            elif command == 'pwd':
                self.pwd(inarray)

    def local_command(self, command, argv):
        if command == 'ls':
            self.local_ls(argv)
        elif command == 'cd':
            self.local_cd(argv)
        elif command == 'pwd':
            self.local_pwd(argv)

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

    def local_ls(self, argv):
        cwd = os.path.curdir
        if not os.path.isdir(cwd):
            print '{} is not a directory'.format(cwd)
        else:
            children = os.listdir(cwd)
            for child in children:
                print child

    def local_cd(self, argv):
        cwd = os.getcwd()
        # fixme make sure this works
        os.chdir(argv[-1])

    def stat(self, argv):
        pass

    def cat(self, argv):
        pass

    def pwd(self, argv):
        print self.cwd

    def local_pwd(self, argv):
        cwd = os.getcwd()
        print cwd

    def cd(self, argv):
        mylog.log_dbg('cd [{}]'.format(argv[1:]))
        dir = argv[-1]
        # if dir in [stat.name for stat in self.subdir_cache]:
        #     self.cwd = os.path.join(self.cwd, dir)
        rel_path = os.path.join(self.cwd, dir)
        response = create_sock_msg_get_response(
            self.tgt_host_ip
            , self.tgt_host_port
            , make_list_files_request(self.cname, self.session_id, rel_path)
        )
        if response['type'] != LIST_FILES_RESPONSE:
            print 'Error during cd:{}'.format(response)
            return
        self.cwd = os.path.join(self.cwd, dir)
        self.cwd = os.path.normpath(self.cwd)
        self.subdir_cache = response['ls']


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
            mylog.set_mylog_verbose()
            args_eaten = 1
        elif arg == '--debug':
            mylog.set_mylog_dbg()
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


def do_prompt(cname, rel_path):
    if rel_path == '.':
        rel_path = '/'
    else:
        rel_path = '/' + rel_path
    return '{}:{}>'.format(cname, rel_path)

