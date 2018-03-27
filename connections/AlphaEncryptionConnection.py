from nacl.encoding import HexEncoder

from common_util import get_mylog
from connections.AbstractConnection import AbstractConnection
from messages.util import get_msg_size, decode_msg_size
from messages.MessageDeserializer import MessageDeserializer
from messages.EnableAlphaEncryptionResponseMessage import EnableAlphaEncryptionResponseMessage
from nacl.public import *
from nacl.utils import *

__author__ = 'Mike'


class AlphaEncryptionConnection(AbstractConnection):
    def __init__(self, connection, client_pkey_hex_str):
        """
        Wraps another AbstractConnection implementation, such that any incoming
            connection type can be "Upgraded" with the ability to seamlessly
            send data with a rudimentary encryption implementation. The
            encryption is not good, but it isn't plaintext, so, that's something.
        :param connection:
        :param client_pkey_hex_str:
        """
        # type: (AbstractConnection, str) -> None
        _log = get_mylog()
        self._conn = connection
        self.client_pk = PublicKey(client_pkey_hex_str, encoder=HexEncoder)
        self._host_keypair = PrivateKey.generate()
        self._box = Box(self._host_keypair, self.client_pk)

    def recv_obj(self):
        _log = get_mylog()
        # The encoded message is the following format:
        # 16 Bytes to encode the message length
        # 24 Bytes (_box.NONCE_SIZE) of data for the nonce
        # N Bytes of actual real payload.
        # First attempt to read 16 bytes that encodes the message length
        data = self._conn.recv_next_data(16)
        length = int(data, 16)
        # Now, try and read the expected amount of data.
        encrypted_packet = self._conn.recv_next_data(length)
        try:
            # The data is hex-encoded, so decrypt it with the HexEncoder.
            decrypted_text = self._box.decrypt(encrypted_packet, None, HexEncoder)
        except nacl.exceptions.CryptoError, e:
            _log.debug('Exception while decoding message.')
            raise e
        return MessageDeserializer.decode_msg(decrypted_text)

    def send_obj(self, message_obj):

        msg_json = message_obj.serialize()
        encrypted_msg = self._box.encrypt(msg_json, None)
        encoded_msg = HexEncoder.encode(encrypted_msg)
        self._conn.send_next_data(encoded_msg)

    def recv_next_data(self, length):
        _log = get_mylog()
        # todo: This looks almost exactly like recv_obj
        data = self._conn.recv_next_data(16)
        encrypted_length = int(data, 16)
        encrypted_packet = self._conn.recv_next_data(encrypted_length)
        try:
            # The data is hex-encoded, so decrypt it with the HexEncoder.
            decrypted_text = self._box.decrypt(encrypted_packet, None, HexEncoder)
        except nacl.exceptions.CryptoError, e:
            _log.debug('Exception while decoding next data.')
            raise e
        return decrypted_text

    def send_next_data(self, data):
        # type: (str) -> int
        # The length of the encrypted message is going to be longer than the
        #   actual payload length. HOWEVER, callers expect the length of the
        #   data that we sent as a result. The length of the data that we sent
        #   is the length of the data before encryption.
        len_data = len(data)
        encrypted_msg = self._box.encrypt(data, None)
        encoded_msg = HexEncoder.encode(encrypted_msg)
        self._conn.send_next_data(encoded_msg)
        return len_data

    def close(self):
        return self._conn.close()

    def send_setup_response(self):
        host_public_key = self._host_keypair.public_key.encode(HexEncoder)
        msg = EnableAlphaEncryptionResponseMessage(host_public_key)
        self._conn.send_obj(msg)
