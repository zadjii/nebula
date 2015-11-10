from connections.AbstractConnection import AbstractConnection
from messages.util import get_msg_size, decode_msg_size
from messages.MessageDeserializer import MessageDeserializer

__author__ = 'Mike'


class RawConnection(AbstractConnection):
    def __init__(self, socket):
        self._socket = socket

    def recv_obj(self):
        data = self._socket.recv(8)
        size = decode_msg_size(data)
        buff = self._socket.recv(size)
        return MessageDeserializer.decode_msg(buff)

    def send_obj(self, message_obj):
        msg_json = message_obj.serialize()
        self._socket.send(get_msg_size(msg_json))
        self._socket.send(msg_json)

    def recv_next_data(self, length):
        return self._socket.recv(length)

    def send_next_data(self, data):
        return self._socket.send(data)

    def close(self):
        return self._socket.close()

