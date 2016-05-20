import socket
from threading import Thread

import sys

from connections.AbstractConnection import AbstractConnection
from host import HOST_WS_PORT
from host.function.network_updates import filter_func
# from messages import decode_msg_size
from host.util import mylog, get_ipv6_list
from messages.util import get_msg_size, decode_msg_size
from messages.MessageDeserializer import MessageDeserializer
from autobahn.asyncio.websocket import WebSocketServerProtocol
# from autobahn.twisted.websocket import WebSocketServerProtocol

__author__ = 'Mike'


class WebsocketConnection(AbstractConnection):
    def __init__(self, connection, ws_server_protocol):
        mylog('top of WSConn.__init__')
        self._socket = connection
        self._ws_server_protocol = ws_server_protocol
        mylog('bottom of WSConn.__init__')

    def recv_obj(self, repeat=False):
        mylog('wsConn.recv_obj')

        size, n_chars = self._really_bad_get_size()
        # first recv the length of the msg from the sock
        length_string = self._socket.recv(n_chars)
        # mylog('These two should be the same:{}={}'.format(size,length_string))
        # then actually get the data
        buff = self._socket.recv(size)

        mylog('wsConn.r_o(1):<{}>'.format(buff))
        obj = MessageDeserializer.decode_msg(buff)
        # mylog('deserialized"{}"[{}]({})'.format(buff, obj, obj.__dict__))
        return obj

    def _really_bad_get_size(self):
        data = '0'
        length = 0
        while data[-1] != '{':
            length += 1
            data = self._socket.recv(length, socket.MSG_PEEK)
            # print '\t\t\t bad get data length {}'.format(data)
            if length > 64:
                raise Exception('Well that\'s a bad packet for sure')
        return int(data[0:length-1]), length-1

    def send_obj(self, message_obj):
        mylog('ws send, {}'.format(message_obj.__dict__))
        msg_json = message_obj.serialize()
        msg_size = get_msg_size(msg_json)  # don't send length over WS
        self._ws_server_protocol.sendMessage(msg_json)
        mylog('bottom of ws send')

    def recv_next_data(self, length):
        return self._socket.recv(length)

    def send_next_data(self, data):
        """Returns the number of bytes sent.
        TODO: determine if the ws actually sent all of len()"""
        self._ws_server_protocol.sendMessage(data)
        return sys.getsizeof(data)

    def close(self):
        self._socket.close()
        self._ws_server_protocol.sendClose()


class MyBigFuckingLieServerProtocol(WebSocketServerProtocol):

    def __init__(self):
        mylog('\x1b[32;41mTop of MBFLSP.__init__\x1b[0m')
        super(MyBigFuckingLieServerProtocol, self).__init__()
        mylog('after super')
        self._internal_port = HOST_WS_PORT+1
        # self._internal_port = HOST_WS_PORT
        self._internal_server_socket = socket.socket()
        # fixme $20 to myself if this vv DOESN'T need to move outside the MBFLSP
        mylog('before bind')
        try:
            self._internal_server_socket.bind(('localhost', self._internal_port))
            # self._internal_server_socket.bind((get_ipv6_list()[0], self._internal_port))
            mylog('\x1b[32;46mbound to {}\x1b[0m'.format(self._internal_port))
        except Exception as e:
            mylog('oof i fucked up')
            mylog(e.message)

        self._internal_server_socket.listen(5)  # todo does this 5 make sense?
        self._internal_conn = None
        self._child_thread = None
        mylog('Bottom of MBFLSP.__init__')

    def onConnect(self, request):
        mylog("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        mylog("WebSocket connection open.")
        temp_socket = socket.socket()
        mylog('MBFLSP.onConnect-0')

        temp_socket.connect(('localhost', self._internal_port))
        mylog('MBFLSP.onConnect-1')
        (conn, addr) = self._internal_server_socket.accept()
        mylog('MBFLSP.onConnect-2')
        ws_conn = WebsocketConnection(temp_socket, self)
        mylog('MBFLSP.onConnect-3')
        self._internal_conn = conn
        self._child_thread = Thread(target=filter_func, args=[ws_conn, addr])
        mylog('before of MBFLSP...thread.start')
        self._child_thread.start()
        # self._child_thread.join() #note: Don't join here, we need to return in
        #   order to be able to get data from onMessage to send to filter_func
        mylog('Bottom of MBFLSP.onOpen')

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))
        self._internal_conn.send(payload)

        # echo back message verbatim
        # self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        mylog("WebSocket closed: {},{},{}".format(wasClean, code, reason))
        # self._internal_conn.send('\0')
        # self._internal_conn.close()
        if self._child_thread is not None:
            self._child_thread.exit()

    def _connectionLost(self, reason):
        mylog('_connectionLost')
        self._internal_conn.send('\0')
        self._internal_conn.close()
        self._internal_server_socket.close()
        WebSocketServerProtocol._connectionLost(self, reason)
