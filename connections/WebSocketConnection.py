import socket
from threading import Thread

import sys

from connections.AbstractConnection import AbstractConnection
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
                mylog('BAD_PACKET:{}'.format(self._socket.recv(64)))
                raise Exception('Well that\'s a bad packet for sure')
        return int(data[0:length-1]), length-1

    def send_obj(self, message_obj):
        mylog('ws send, {}'.format(message_obj.__dict__))
        msg_json = message_obj.serialize()
        msg_size = get_msg_size(msg_json)  # don't send length over WS
        self._ws_server_protocol.sendMessage(msg_json)
        mylog('bottom of ws send_obj')

    def recv_next_data(self, length):
        return self._socket.recv(length)

    def send_next_data(self, data):
        """Returns the number of bytes sent.
        TODO: determine if the ws actually sent all of len()"""
        # data = data.encode('utf8')
        length = len(data)

        # self._ws_server_protocol.beginMessage(isBinary=True)
        # self._ws_server_protocol.beginMessageFrame(length)
        # self._ws_server_protocol.sendMessageFrameData(data)
        self._ws_server_protocol.sendMessage(data, isBinary=True)
        self._ws_server_protocol.sendPing()
        # mylog('bottom of ws send_next_data, "{}"[{}]'.format(data, length))
        # mylog('bottom of ws send_next_data')
        return length

    def close(self):
        self._socket.close()
        self._ws_server_protocol.sendClose()


class MyBigFuckingLieServerProtocol(WebSocketServerProtocol):
    net_thread = None

    def __init__(self):
        mylog('Top of MBFLSP.__init__', '32;41')
        super(MyBigFuckingLieServerProtocol, self).__init__()
        self._internal_client_socket = None
        mylog('Bottom of MBFLSP.__init__')

    def onConnect(self, request):
        mylog("Client connecting: {0}".format(request.peer))
        self._internal_client_socket = socket.socket()
        self._internal_client_socket.connect(
            ('localhost'
             , MyBigFuckingLieServerProtocol.net_thread._ws_internal_port))
        MyBigFuckingLieServerProtocol.net_thread.add_ws_conn(self)
        mylog('Bottom of MBFLSP.onConnect')


    def onOpen(self):
        mylog("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            mylog("Binary message received: {0} bytes".format(len(payload)))
        else:
            mylog("Text message received: {0}".format(payload.decode('utf8')))
        self._internal_client_socket.send(payload)
        MyBigFuckingLieServerProtocol.net_thread.signal_host()

        # echo back message verbatim
        # self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        mylog("WebSocket closed: (wasClean, code, reason) = ({},{},{})".format(wasClean, code, reason))
        self._internal_client_socket.send('\0')
        self._internal_client_socket.close()
        # if self._child_thread is not None:
        #     self._child_thread.exit()

    # def _connectionLost(self, reason):
    #     mylog('_connectionLost')
    #     self._internal_conn.send('\0')
    #     self._internal_conn.close()
    #     self._internal_server_socket.close()
    #     WebSocketServerProtocol._connectionLost(self, reason)
