import unittest

from common_util import INVALID_HOST_ID
from connections.AbstractConnection import AbstractConnection
from messages import NewHostMessage, AssignHostIdMessage, HostMoveRequestMessage, HostMoveResponseMessage
from messages.BaseMessage import BaseMessage
from remote.models.Cloud import *
from remote.models.User import *
from remote.models.Host import *
from remote.RemoteController import RemoteController
from remote.NebrInstance import NebrInstance

from ExpectedObjConnection import ExpectedObjConnection


class RemoteControllerTests(unittest.TestCase):
    def expectResponse(self, request, response):
        # type: (BaseMessage, BaseMessage) -> ExpectedObjConnection
        conn = ExpectedObjConnection(self)
        conn.in_obj = request
        conn.expected_obj = response
        return conn

    def setUp(self):
        self.instance = NebrInstance(working_dir=None, unittesting=True)
        self.instance.disable_ssl = True
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
        self.db.session.add(cloud)
        self.db.session.commit()
        self.db.session.commit()

    def test_default_setup(self):
        self.setup_default_clouds()
        self.assertEqual(2, len(self.db.session.query(Cloud).all()))

    def test_filter_message_works(self):
        """
        This is just a canary test to make sure that we can test filtering messages like this
        """
        self.setup_default_clouds()
        req = HostMoveRequestMessage(INVALID_HOST_ID, '1::1', 'my_fake_cert_request')
        resp = HostMoveResponseMessage(1, None)
        conn = self.expectResponse(req, resp)
        self.controller.filter_func(conn, '')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
