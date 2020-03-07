import unittest

from connections.AbstractConnection import AbstractConnection


class ExpectedObjConnection(AbstractConnection):
    def __init__(self, testcase):
        # type: (unittest.TestCase) -> None
        self._testcase = testcase
        self.expected_obj = None
        self.in_obj = None
        self.send_callback = None
        self.recv_callback = None

    def send_obj(self, message_obj):
        """
        When the host tries to send a message, we'll check that the message is
        the same as whatever one we're expecting.
        :param message_obj:
        :return:
        """
        if self.send_callback is not None:
            self.send_callback(message_obj)
        else:
            self._testcase.assertNotEqual(None, self.expected_obj)
            self._testcase.assertEqual(self.expected_obj.__dict__, message_obj.__dict__)

    def recv_obj(self):
        if self.recv_callback is not None:
            return self.recv_callback()
        else:
            in_obj = self.in_obj
            self.in_obj = None
            return in_obj

    def recv_next_data(self, length):
        self._testcase.assertFalse(True, 'recv_next_data isnt implemented yet. Avoid testing that scenario with this.')

    def send_next_data(self, data):
        self._testcase.assertFalse(True, 'send_next_data isnt implemented yet. Avoid testing that scenario with this.')

    def close(self):
        pass

