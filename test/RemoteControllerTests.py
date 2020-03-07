import unittest

from connections.AbstractConnection import AbstractConnection
from messages.BaseMessage import BaseMessage
from remote.models.Cloud import *
from remote.models.User import *
from remote.RemoteController import RemoteController
from remote.NebrInstance import NebrInstance


class RemoteControllerTests(unittest.TestCase):
    ZADJII_HOME = '/user/home/zadjii/nebula/zadjii/home'

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
