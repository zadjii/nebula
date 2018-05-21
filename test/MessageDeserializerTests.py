import logging
import os
import unittest
import json
from messages import *
from messages.MessageDeserializer import MessageDeserializer

class MessageDeserializerTests(unittest.TestCase):

    def test_easy(self):
        msg_obj = ClientSessionRequestMessage('asdf', 'asdf')
        roundtrip = MessageDeserializer.decode_msg(msg_obj.serialize())
        self.assertEqual(msg_obj.__dict__, roundtrip.__dict__)

    def test_raw(self):
        expected_msg = ClientSessionRequestMessage('asdf', 'asdf')
        test_text = '{"type":26, "uname":"asdf", "passw":"asdf"}'
        roundtrip = MessageDeserializer.decode_msg(test_text)
        self.assertEqual(expected_msg.__dict__, roundtrip.__dict__)

    def test_bad_type(self):
        expected_msg = ClientSessionRequestMessage('asdf', 'asdf')
        test_text = '{"type":27, "uname":"asdf", "passw":"asdf"}'
        roundtrip = MessageDeserializer.decode_msg(test_text)
        self.assertEqual(expected_msg.__dict__, roundtrip.__dict__)

    def test_bad_key(self):
        expected_msg = ClientSessionRequestMessage('asdf', 'asdf')
        test_text = '{"type":26, "cname":"asdf", "passw":"asdf"}'
        roundtrip = MessageDeserializer.decode_msg(test_text)
        self.assertEqual(expected_msg.__dict__, roundtrip.__dict__)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
