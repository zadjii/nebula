import logging
import os
from datetime import timedelta
import unittest

from host import models
from .HostDbTestBase import HostDbTestBase
from host.models.Remote import *
from host.models.Cloud import *
from host.models.FileNode import *
from host.HostController import HostController
from host.NebsInstance import NebsInstance


class HostControllerTests(unittest.TestCase):

    def setUp(self):
        self.instance = NebsInstance(working_dir=None, unittesting=True)
        self.instance.get_db().create_all()
        self.db = self.instance.get_db()
        self.controller = HostController(self.instance)

    def tearDown(self):
        pass

    def test_ctor(self):
        self.assertNotEqual(None, self.controller)
        # Make sure that the controller's instance's DB is the same as what we created
        self.assertNotEqual(None, self.db)
        self.assertEqual('sqlite:///', self.controller.get_instance()._db_uri())
        self.assertEqual(self.db.Base.metadata.tables, self.controller.get_instance().get_db().Base.metadata.tables)
        self.assertEqual(self.db.Base.metadata, self.controller.get_instance().get_db().Base.metadata)

    def test_create_node(self):
        node = FileNode('foo')
        print(self.db.Base)
        print(self.db.Base.metadata)
        self.db.session.add(node)
        self.db.session.commit()

    def test_find_mirror_for_file(self):
        zadjii_home = Cloud('zadjii', 'home', '/user/home/zadjii/nebula/zadjii/home')
        zadjii_work = Cloud('zadjii', 'work', '/user/home/zadjii/nebula/zadjii/work')
        claire_home = Cloud('claire', 'home', '/user/home/claire/nebula/claire/home')
        self.db.session.add(zadjii_home)
        self.db.session.add(zadjii_work)
        self.db.session.add(claire_home)
        self.db.session.commit()

        c = self.controller._find_mirror_for_file('/user/home/zadjii/nebula/zadjii/home')
        self.assertNotEqual(None, c)
        self.assertEqual(zadjii_home.id, c.id)
        c = self.controller._find_mirror_for_file('/user/home/zadjii/nebula/zadjii/home/foo')
        self.assertNotEqual(None, c)
        self.assertEqual(zadjii_home.id, c.id)
        c = self.controller._find_mirror_for_file('/user/home/zadjii/nebula/zadjii/home/foo/bar')
        self.assertNotEqual(None, c)
        self.assertEqual(zadjii_home.id, c.id)
        c = self.controller._find_mirror_for_file('/user/home/zadjii/nebula/zadjii/work/foo/bar')
        self.assertNotEqual(None, c)
        self.assertEqual(zadjii_work.id, c.id)
        c = self.controller._find_mirror_for_file('/user/home/claire/nebula/claire/home/foo/bar')
        self.assertNotEqual(None, c)
        self.assertEqual(claire_home.id, c.id)

        c = self.controller._find_mirror_for_file('/user/home/')
        self.assertEqual(None, c)
        c = self.controller._find_mirror_for_file('/user/home/zadjii')
        self.assertEqual(None, c)
        c = self.controller._find_mirror_for_file('/user/home/zadjii/nebula')
        self.assertEqual(None, c)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
