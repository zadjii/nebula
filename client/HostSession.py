import socket
from connections.RawConnection import RawConnection
from host.util import setup_remote_socket
from messages import *
from msg_codes import *
from common_util import *


def create_sock_msg_get_response(ip, port, msg):
    conn = create_sock_and_send(ip, port, msg)
    response = conn.recv_obj()
    conn.close()
    return response


def create_sock_and_send(ip, port, msg):
    # todo: replace this block with a single helper, reuse in mirror.py, etc.
    is_ipv6 = ':' in ip
    sock_type = socket.AF_INET6 if is_ipv6 else socket.AF_INET
    sock_addr = (ip, port, 0, 0) if is_ipv6 else (ip, port)
    host_sock = socket.socket(sock_type, socket.SOCK_STREAM)
    host_sock.connect(sock_addr)
    conn = RawConnection(host_sock)

    conn.send_obj(msg)
    return conn


class RemoteSession(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def _get_client_session(self, uname, password):
        try:
            rem_sock = setup_remote_socket(self._host, self._port)
            rem_conn = RawConnection(rem_sock)
            request = ClientSessionRequestMessage(uname, password)
            rem_conn.send_obj(request)
            response = rem_conn.recv_obj()
            if not (response.type == CLIENT_SESSION_RESPONSE):
                raise Exception('remote did not respond with success')
            return ResultAndData(True, response)
        except Exception, e:
            return ResultAndData(False, e)

    def create_client_session(self, uname, password):
        # type: (str, str) -> ResultAndData
        # type: (str, str) -> ResultAndData(True, HostSession)
        # type: (str, str) -> ResultAndData(False, Exception)
        rd = self._get_client_session(uname, password)
        # somehow get SID
        sid = None
        if rd.success:
            sid = rd.data.sid
            host_session = HostSession(sid, self)
            host_session.remote_session = self
            rd = Success(host_session)
        return rd

    def get_client_host(self, sid, cloud_uname, cname):
        try:
            rem_sock = setup_remote_socket(self._host, self._port)
            rem_conn = RawConnection(rem_sock)

            msg = ClientGetCloudHostRequestMessage(sid, cloud_uname, cname)
            rem_conn.send_obj(msg)
            response = rem_conn.recv_obj()
            if not (response.type == CLIENT_GET_CLOUD_HOST_RESPONSE):
                raise Exception('remote did not respond with success CGCR')
            return ResultAndData(True, response)
        except Exception, e:
            return ResultAndData(False, e)


class HostSession(object):

    def __init__(self, sid, remote_session):
        self.sid = sid
        self.cloud_uname = None
        self.cname = None
        self.ip = None
        self.port = None
        self.remote_session = remote_session
        self._connected = False

    def get_host(self, cloud_uname, cname):
        self.cloud_uname = cloud_uname
        self.cname = cname
        rd = self.remote_session.get_client_host(self.sid, self.cloud_uname, self.cname)
        if rd.success:
            self.ip = rd.data.ip
            self.port = rd.data.port
        return rd

    def connect(self):
        socket_type = socket.AF_INET
        sock_addr = (self.ip, self.port)
        if ':' in self.ip:
            socket_type = socket.AF_INET6
            sock_addr = (self.ip, self.port, 0, 0)

        host_sock = socket.socket(socket_type, socket.SOCK_STREAM)
        host_sock.connect(sock_addr)
        conn = RawConnection(host_sock)
        self._connected = True
        return conn

    def ls(self, path):
        print('start of ls')
        msg = ListFilesRequestMessage(self.sid, self.cloud_uname, self.cname, path)
        response = create_sock_msg_get_response(
            self.ip
            , self.port
            , msg
        )
        print('end of ls')
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
        # log_text('making directory for {}/{}, {}'.format(self.cloud_uname, self.cname, path))
        msg = ClientFilePutMessage(self.sid, self.cloud_uname, self.cname, path)
        conn = create_sock_and_send(self.ip, self.port, msg)
        msg = ClientFileTransferMessage(self.sid, self.cloud_uname, self.cname, path, 0, True)
        conn.send_obj(msg)
        conn.send_obj(ClientFileTransferMessage(self.sid, self.cloud_uname, self.cname, None, None, None))
        # log_text('Sent CFT message')
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
