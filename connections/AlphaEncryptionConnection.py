from nacl.encoding import HexEncoder

from common_util import get_mylog
from connections.AbstractConnection import AbstractConnection
from messages.util import get_msg_size, decode_msg_size
from messages.MessageDeserializer import MessageDeserializer
from messages.EnableAlphaEncryptionResponseMessage import EnableAlphaEncryptionResponseMessage
from nacl.public import *
from nacl.utils import *

__author__ = 'Mike'


# clients are going to preface sends with 16 chars to say how long the message is
# this is 2 chars/byte * 8 bytes = 16 chars
# the chars will be a hex encoding of the message length


class AlphaEncryptionConnection(AbstractConnection):
    def __init__(self, connection, client_pkey_hex_str):
        # type: (AbstractConnection, str) -> None
        _log = get_mylog()
        # _log.debug('Creating AlphaEncryptionConnection')
        self._conn = connection
        # _log.debug('decoded pk = "{}"'.format(HexEncoder.decode(client_pkey_hex_str)))
        self.client_pk = PublicKey(client_pkey_hex_str, encoder=HexEncoder)
        # self.client_pk = PublicKey(client_pkey_hex_str)
        # _log.debug('client_pk="{}"'.format(self.client_pk))
        self._host_keypair = PrivateKey.generate()
        self._box = Box(self._host_keypair, self.client_pk)
        # skbob = PrivateKey.generate()
        # pkbob = skbob.public_key

    def recv_obj(self):
        _log = get_mylog()
        data = self._conn.recv_next_data(16)
        # _log.debug('Encoded length:{}'.format(data))
        # len_str = HexEncoder.decode(data)
        # _log.debug('len_str={}'.format(len_str))
        # len = int(len_str)
        length = int(data, 16)
        # _log.debug('Encrypted length:{}'.format(length))
        encrypted_packet = self._conn.recv_next_data(length)
        # _log.debug('Encrypted data:"{}"'.format(encrypted_packet))
        # _log.debug('nonce_size:{}'.format(self._box.NONCE_SIZE))
        hex_decoded = HexEncoder.decode(encrypted_packet)
        # _log.debug('decoded ecrypted:{}'.format(hex_decoded))
        nonce = hex_decoded[:self._box.NONCE_SIZE]
        payload = hex_decoded[self._box.NONCE_SIZE:]
        # _log.debug('nonce="{}"'.format(HexEncoder.encode(nonce)))
        # _log.debug('payload="{}"'.format(HexEncoder.encode(payload)))
        try:
            decrypted_text = self._box.decrypt(encrypted_packet, None, HexEncoder)
            # decrypted_text = self._box.decrypt(encrypted_packet)
            # _log.debug('Dencrypted data:"{}"'.format(decrypted_text))
            # _log.debug('Dencrypted data:"{}"'.format(HexEncoder.encode(decrypted_text)))
        except nacl.exceptions.CryptoError, e:
            _log.debug('Exception while decoding message.')
            raise e
        # data = self._socket.recv(8)
        # size = decode_msg_size(data)
        # buff = self._socket.recv(size)
        return MessageDeserializer.decode_msg(decrypted_text)

    def send_obj(self, message_obj):
        _log = get_mylog()

        msg_json = message_obj.serialize()
        # _log.debug('msg_json="{}"'.format(msg_json))
        # _log.debug('payload="{}"'.format(HexEncoder.encode(msg_json)))

        encrypted_msg = self._box.encrypt(msg_json, None)
        # _log.debug('encrypted_msg="{}"'.format(encrypted_msg))

        nonce = encrypted_msg[:self._box.NONCE_SIZE]
        # _log.debug('nonce?="{}"'.format(HexEncoder.encode(nonce)))

        encoded_msg = HexEncoder.encode(encrypted_msg)
        # _log.debug('encoded_msg="{}"'.format(encoded_msg))

        self._conn.send_next_data(encoded_msg)
        # self._socket.send(get_msg_size(msg_json))
        # self._socket.send(msg_json)

    def recv_next_data(self, length):
        _log = get_mylog()
        # _log.debug('recv_next_data({})'.format(length))
        data = self._conn.recv_next_data(16)
        encrypted_length = int(data, 16)

        encrypted_packet = self._conn.recv_next_data(encrypted_length)
        # _log.debug('encrypted_packet:{}'.format(encrypted_packet))
        hex_decoded = HexEncoder.decode(encrypted_packet)
        # _log.debug('decoded ecrypted:{}'.format(hex_decoded))
        nonce = hex_decoded[:self._box.NONCE_SIZE]
        payload = hex_decoded[self._box.NONCE_SIZE:]
        # _log.debug('nonce="{}"'.format(HexEncoder.encode(nonce)))
        # _log.debug('payload="{}"'.format(HexEncoder.encode(payload)))

        decrypted_text = self._box.decrypt(encrypted_packet, None, HexEncoder)
        # _log.debug('decrypted_text="{}"'.format(decrypted_text))
        # _log.debug('decrypted_text_len="{}"'.format(len(decrypted_text)))
        # _log.debug('length="{}"'.format(length))

        return decrypted_text

    def send_next_data(self, data):
        _log = get_mylog()
        # _log.debug('send_next_data')
        len_data = len(data)
        # _log.debug('len(data)={}'.format(len(data)))

        encrypted_msg = self._box.encrypt(data, None)
        # _log.debug('encrypted_msg="{}"'.format(encrypted_msg))

        nonce = encrypted_msg[:self._box.NONCE_SIZE]
        # _log.debug('nonce?="{}"'.format(HexEncoder.encode(nonce)))

        encoded_msg = HexEncoder.encode(encrypted_msg)
        # _log.debug('encoded_msg="{}"'.format(encoded_msg))
        # _log.debug('len(encoded_msg)={}'.format(len(encoded_msg)))

        self._conn.send_next_data(encoded_msg)
        return len_data

    def close(self):
        return self._conn.close()

    def send_setup_response(self):
        _log = get_mylog()
        # _log.debug('top')
        # host_public_key = HexEncoder.encode(self._host_keypair.public_key)
        host_public_key = self._host_keypair.public_key.encode(HexEncoder)
        # _log.debug('encoded pk: [{}]'.format(host_public_key))
        msg = EnableAlphaEncryptionResponseMessage(host_public_key)
        # _log.debug('response_message = "{}"'.format(msg.serialize()))
        # self.send_obj(msg)
        self._conn.send_obj(msg)
        # _log.debug('finished setup')
