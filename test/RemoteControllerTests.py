import unittest

from connections.AbstractConnection import AbstractConnection
from messages.BaseMessage import BaseMessage
from remote.models.Cloud import *
from remote.models.User import *
from remote.RemoteController import RemoteController
from remote.NebrInstance import NebrInstance


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


class RemoteControllerTests(unittest.TestCase):
    ZADJII_HOME = '/user/home/zadjii/nebula/zadjii/home'

    def expectResponse(self, request, response):
        # type: (BaseMessage, BaseMessage) -> ExpectedObjConnection
        conn = ExpectedObjConnection(self)
        conn.in_obj = request
        conn.expected_obj = response
        return conn

    def setUp(self):
        self.instance = NebrInstance(working_dir=None, unittesting=True)
        self.instance.get_db().create_all()
        self.db = self.instance.get_db()
        self.controller = RemoteController(self.instance)

    def tearDown(self):
        pass

    def test_ctor(self):
        self.assertNotEqual(None, self.controller)
        # Make sure that the controller's instance's DB is the same as what we created
        self.assertNotEqual(None, self.db)
        self.assertEqual('sqlite:///', self.controller.get_instance()._db_uri())
        self.assertEqual(self.db.Base.metadata.tables, self.controller.get_instance().get_db().Base.metadata.tables)
        self.assertEqual(self.db.Base.metadata, self.controller.get_instance().get_db().Base.metadata)

    def test_create_user(self):
        user = User()
        user.name = 'zadjii'
        self.db.session.add(user)
        self.db.session.commit()
        self.assertEqual(1, len(self.db.session.query(User).all()))


    def test_create_cloud(self):
        user = User()
        user.name = 'zadjii'
        self.db.session.add(user)
        cloud = Cloud(user)
        self.db.session.add(cloud)
        self.db.session.commit()
        self.assertEqual(1, len(self.db.session.query(Cloud).all()))

    def setup_default_clouds(self):
        user = User()
        user.name = 'zadjii'
        self.db.session.add(user)
        cloud = Cloud(user)
        cloud.name = 'home'
        self.db.session.add(cloud)
        cloud = Cloud(user)
        cloud.name = 'work'
        self.db.session.commit()

    def test_default_setup(self):
        self.setup_default_clouds()
        self.assertEqual(2, len(self.db.session.query(Cloud).all()))

def main():
    unittest.main()


if __name__ == '__main__':
    main()
