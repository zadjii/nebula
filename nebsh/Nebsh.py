import getpass
import socket
import os
from stat import S_ISDIR
from sys import stdin
from connections.RawConnection import RawConnection
from host import REMOTE_PORT
from host.util import setup_remote_socket
# from msg_codes import *
from messages import *
from msg_codes import CLIENT_SESSION_RESPONSE, LIST_FILES_RESPONSE,\
    STAT_FILE_RESPONSE
from nebsh import mylog


__author__ = 'Mike'


class NebshClient(object):
    def __init__(self, args):
        self.testing, self.rem_addr, self.rem_port, self.cname =\
            process_args(args)
        # self.rem_sock = None
        # self.host_sock = None
        self.rem_conn = None
        self.host_conn = None

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

        rem_sock = setup_remote_socket(self.rem_addr, self.rem_port)
        self.rem_conn = RawConnection(rem_sock)
        # request = make_client_session_request(self.cname, self.username, password)
        request = ClientSessionRequestMessage(self.cname, self.username, password)
        # send_msg(request, self.rem_sock)
        self.rem_conn.send_obj(request)
        response = self.rem_conn.recv_obj()
        # response = recv_msg(self.rem_sock)
        # print '__ resp:{}__'.format(response)
        if not (response.type == CLIENT_SESSION_RESPONSE):
            raise Exception('remote did not respond with success')
        self.session_id = response.sid
        self.tgt_host_ip = response.ip
        self.tgt_host_port = response.port
        self.main_loop()

    def main_loop(self):
        msg = ListFilesRequestMessage(self.cname, self.session_id, '.')
        response = create_sock_msg_get_response(
            self.tgt_host_ip
            , self.tgt_host_port
            , msg
        )
        mylog.log_dbg(response.__dict__)
        self.cwd = response.fpath
        self.subdir_cache = response.ls
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
            elif command == 'nput':
                self.nput(inarray)

    def local_command(self, command, argv):
        if command == 'ls':
            self.local_ls(argv)
        elif command == 'cd':
            self.local_cd(argv)
        elif command == 'pwd':
            self.local_pwd(argv)

    def nput(self, argv):
        """ nput [-r] <LOCAL path> <NEB path> """
        if len(argv) < 3:  # nput, from, to
            print 'not enough args for nput'
            return
        recursive = '-r' in argv
        local_path = argv[-2]
        local_file = os.path.basename(local_path)
        mylog.log_dbg('localpath={}->{}'.format(local_path, local_file))
        rel_path = argv[-1]
        neb_file = os.path.join(rel_path, local_file)
        mylog.log_dbg('nebpath={}->{}'.format(rel_path, neb_file))

        msg = ClientFilePutMessage(self.cname, self.session_id, neb_file)
        host_sock = create_sock_and_send(
            self.tgt_host_ip
            , self.tgt_host_port
            , msg
        )

        send_file_to_host(self.session_id, self.cname, local_path, neb_file, recursive, host_sock)
        mylog.log_dbg('bottom of nput?')
        # send_msg(
        #     make_client_file_transfer(self.cname, self.session_id, rel_path, is_dir, filesize)
        #     , host_sock
        # )
        complete_sending_files(self.cname, self.session_id, host_sock)

    def ls(self, argv):
        # print 'ls [{}]'.format(argv[1:])
        dir = argv[-1]
        # print dir
        if dir == 'ls':
            dir = '.'
        rel_path = os.path.join(self.cwd, dir)
        msg = ListFilesRequestMessage(self.cname, self.session_id, rel_path)
        response = create_sock_msg_get_response(
            self.tgt_host_ip
            , self.tgt_host_port
            , msg
        )
        if response.type != LIST_FILES_RESPONSE:
            print 'Error during ls:{}'.format(response)
            return
        # print response
        if response is not None and response.ls is not None:
            for child in response.ls:
                print child['name']
        else:
            if response.stat is None:
                print '{} was not found'.format(rel_path)
            else:  # I don't this this block is ever hit
                print '{} is not a directory'.format(rel_path)
            mylog.log_dbg(response.__dict__)

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
        # FIXME `cd \` or `cd /` takes you to the root of the Host FS.
        # cont    this is like, REALLY bad. Gotta make sure any requests
        # cont    don't escape the cloud's file tree.
        # cont    like, makes sure every single request is a subdir of the root
        mylog.log_dbg('cd [{}]'.format(argv[1:]))
        dir = argv[-1]
        # if dir in [stat.name for stat in self.subdir_cache]:
        #     self.cwd = os.path.join(self.cwd, dir)
        rel_path = os.path.join(self.cwd, dir)
        msg = ListFilesRequestMessage(self.cname, self.session_id, rel_path)
        response = create_sock_msg_get_response(
            self.tgt_host_ip
            , self.tgt_host_port
            , msg
        )
        if response.type != LIST_FILES_RESPONSE:
            print 'Error during cd:{}'.format(response)
            return
        mylog.log_dbg(response.__dict__)
        if response.stat is not None:
            self.cwd = os.path.join(self.cwd, dir)
            self.cwd = os.path.normpath(self.cwd)
            self.subdir_cache = response.ls


def create_sock_msg_get_response(ip, port, msg):
    conn = create_sock_and_send(ip, port, msg)
    response = conn.recv_obj()
    conn.close()
    return response


def create_sock_and_send(ip, port, msg):
    host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_sock.connect((ip, port))
    conn = RawConnection(host_sock)
    conn.send_obj(msg)
    return conn


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
                print 'not enough args supplied to -r'
                nebsh_usage()
                exit()
            host = argv[1]
            args_eaten = 2
        elif arg == '-p':
            if args_left < 2:
                # throw some exception
                print 'not enough args supplied to -p'
                nebsh_usage()
                exit()
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
        print 'Must specify a cloud name to mirror'
        nebsh_usage()
        exit()
    if host is None:
        print 'Must specify a host to mirror from'
        nebsh_usage()
        exit()
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


def send_file_to_host(session_id, cloudname, local_path, neb_path, recurse, socket_conn):
    """
    Assumes that the other host was already verified, and the cloud is non-null
    """
    req_file_stat = os.stat(local_path)

    # relative_pathname = os.path.relpath(filepath, cloud.root_directory)
    # print 'relpath({}) in \'{}\' is <{}>'.format(filepath, cloud.name, relative_pathname)

    req_file_is_dir = S_ISDIR(req_file_stat.st_mode)
    if req_file_is_dir:
        # if neb_path != '.':  # todo: I think this we don't need; should test.
        # cont either way, need to determine cases for '.', '/', '..', etc todo<
        msg = ClientFileTransferMessage(
            cloudname
            , session_id
            , neb_path
            , req_file_is_dir
            , 0
        )
        socket_conn.send_obj(msg)
        # send_msg(
        #     make_client_file_transfer(
        #         cloudname
        #         , session_id
        #         , neb_path
        #         , req_file_is_dir
        #         , 0
        #     )
        #     , socket_conn
        # )
        if recurse:
            subdirectories = os.listdir(local_path)
            mylog.log_dbg('Sending children of <{}>={}'.format(local_path, subdirectories))
            for f in subdirectories:
                send_file_to_host(
                    session_id
                    , cloudname
                    , os.path.join(local_path, f)
                    , os.path.join(neb_path, f)
                    , recurse
                    , socket_conn
                )
    else:
        req_file_size = req_file_stat.st_size
        requested_file = open(local_path, 'rb')
        msg = ClientFileTransferMessage(
            cloudname
            , session_id
            , neb_path
            , req_file_is_dir
            , req_file_size
        )
        socket_conn.send_obj(msg)
        # send_msg(
        #     make_client_file_transfer(
        #         cloudname
        #         , session_id
        #         , neb_path
        #         , req_file_is_dir
        #         , req_file_size
        #     )
        #     , socket_conn
        # )
        l = 1
        while l:
            new_data = requested_file.read(1024)
            l = socket_conn.send(new_data)
            # mylog(
            #     '[{}]Sent {}B of file<{}> data'
            #     .format(cloud.my_id_from_remote, l, filepath)
            # )
        mylog.log_dbg(
            '[{}]Sent <{}> data to host'
            .format(session_id, local_path)
        )

        requested_file.close()


def complete_sending_files(cloudname, session_id, socket_conn):
    msg = ClientFileTransferMessage(cloudname, session_id, None, None, None)
    socket_conn.send_obj(msg)
    # send_msg(
    #     make_client_file_transfer(cloudname, session_id, None, None, None)
    #     , socket_conn
    # )
    mylog.log_dbg('[{}] completed sending files to [{}]'
                  .format(session_id, cloudname))

