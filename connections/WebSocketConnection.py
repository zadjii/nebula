import socket
from threading import Thread
from connections.AbstractConnection import AbstractConnection
from host import HOST_WS_PORT
from host.function.network_updates import filter_func
# from messages import decode_msg_size
from host.util import mylog
from messages.util import get_msg_size, decode_msg_size
from messages.MessageDeserializer import MessageDeserializer

__author__ = 'Mike'


class WebsocketConnection(AbstractConnection):
    def __init__(self, connection, ws_server_protocol):
        mylog('top of WSConn.__init__')
        self._socket = connection
        self._ws_server_protocol = ws_server_protocol
        mylog('bottom of WSConn.__init__')

    def recv_obj(self, repeat=False):
        mylog('wsConn.recv_obj')
        # data = self._socket.recv(8)
        #
        # mylog('wsConn.r_o(0):"<{}>'.format(data))
        # if data == '' and not repeat:
        #     mylog('repeating')
        #     return self.recv_obj(True)
        # size = decode_msg_size(data)
        size, n_chars = self._really_bad_get_size()
        self._socket.recv(n_chars)
        buff = self._socket.recv(size)
        mylog('wsConn.r_o(1):<{}>'.format(buff))
        obj = MessageDeserializer.decode_msg(buff)
        mylog('deserialized"{}"[{}]({})'.format(buff, obj, obj.__dict__))
        return obj

    def _really_bad_get_size(self):
        data = '0'
        length = 0
        while data[-1] != '{':
            length += 1
            data = self._socket.recv(length, socket.MSG_PEEK)
        return int(data[0:length-1]), length-1

    def send_obj(self, message_obj):
        mylog('ws send, {}'.format(message_obj.__dict__))
        msg_json = message_obj.serialize()
        # self._socket.send(get_msg_size(msg_json))
        # self._socket.send(msg_json)
        msg_size = get_msg_size(msg_json)
        self._ws_server_protocol.sendMessage(msg_size + msg_json)
        mylog('bottom of ws send')

    def recv_next_data(self, length):
        return self._socket.recv(length)

    def send_next_data(self, data):
        return self._ws_server_protocol.sendMessage(data)

    def close(self):
        self._socket.close()


from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory


class MyBigFuckingLieServerProtocol(WebSocketServerProtocol):

    def __init__(self):
        super(MyBigFuckingLieServerProtocol, self).__init__()
        mylog('Top of MBFLSP.__init__')
        self._internal_port = HOST_WS_PORT
        self._internal_server_socket = socket.socket()
        # fixme $20 to myself if this vv DOESN'T need to move outside the MBFLSP
        self._internal_server_socket.bind(('localhost', HOST_WS_PORT))
        self._internal_server_socket.listen(5)  # todo does this 5 make sense?
        self._internal_conn = None
        mylog('Bottom of MBFLSP.__init__')

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))
        temp_socket = socket.socket()
        mylog('MBFLSP.onConnect-0')

        temp_socket.connect(('localhost', self._internal_port))
        mylog('MBFLSP.onConnect-1')
        (conn, addr) = self._internal_server_socket.accept()
        mylog('MBFLSP.onConnect-2')
        # todo wrap the conn in a WSConn
        ws_conn = WebsocketConnection(temp_socket, self)
        mylog('MBFLSP.onConnect-3')
        self._internal_conn = conn
        thread = Thread(target=filter_func, args=[ws_conn, addr])
        mylog('MBFLSP.onConnect-4')
        # thread = Thread(target=filter_func, args=[ws_conn, addr]) #TODO turnon

        mylog('before of MBFLSP...thread.start')
        thread.start()
        # thread.join()
        mylog('Bottom of MBFLSP.onConnect')

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))
        self._internal_conn.send(payload)

        # echo back message verbatim
        # self.sendMessage(payload, isBinary)


    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        self._internal_conn.close()


