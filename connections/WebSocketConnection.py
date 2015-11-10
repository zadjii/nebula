import socket
from threading import Thread
from connections.AbstractConnection import AbstractConnection
from host import HOST_WS_PORT
from host.function.network_updates import filter_func
# from messages import decode_msg_size
from messages.util import get_msg_size, decode_msg_size
from messages.MessageDeserializer import MessageDeserializer

__author__ = 'Mike'


class WebsocketConnection(AbstractConnection):
    def __init__(self, connection, ws_server_protocol):
        self._socket = connection
        self._ws_server_protocol = ws_server_protocol


    def recv_obj(self):
        data = self._socket.recv(8)
        size = decode_msg_size(data)
        buff = self._socket.recv(size)
        return MessageDeserializer.decode_msg(buff)

    def send_obj(self, message_obj):
        msg_json = message_obj.serialize()
        # self._socket.send(get_msg_size(msg_json))
        # self._socket.send(msg_json)
        msg_size = get_msg_size(msg_json)
        self._ws_server_protocol.sendMessage(msg_size + msg_json)

    def recv_next_data(self, length):
        return self._socket.recv(length)

    def send_next_data(self, data):
        return self._ws_server_protocol.sendMessage(data)


from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

class MyBigFuckingLieServerProtocol(WebSocketServerProtocol):

    def __init__(self):
        super(MyBigFuckingLieServerProtocol, self).__init__()
        print 'MBFLSP.__init__'
        self._internal_port = HOST_WS_PORT
        self._internal_server_socket = socket.socket()
        self._internal_server_socket.bind(('localhost', HOST_WS_PORT))
        self._internal_server_socket.listen(5)  # todo does this 5 make sense?
        self._internal_conn = None

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))
        temp_socket = socket.socket()
        temp_socket.connect(('localhost', self._internal_port))
        (conn, addr) = self._internal_server_socket.accept()
        # todo wrap the conn in a WSConn
        ws_conn = WebsocketConnection(temp_socket, self)
        self._internal_conn = conn
        thread = Thread(target=filter_func, args=[conn, addr])
        # thread = Thread(target=filter_func, args=[ws_conn, addr]) #TODO turnon

        thread.start()
        thread.join()

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


