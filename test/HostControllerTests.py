import unittest

from messages.BaseMessage import BaseMessage
from host.models.Cloud import *
from host.models.FileNode import *
from host.HostController import HostController
from host.NebsInstance import NebsInstance
from ExpectedObjConnection import ExpectedObjConnection


class HostControllerTests(unittest.TestCase):
    ZADJII_HOME = '/user/home/zadjii/nebula/zadjii/home'
    ZADJII_WORK = '/user/home/zadjii/nebula/zadjii/work'
    CLAIRE_HOME = '/user/home/claire/nebula/claire/home'

    def expectResponse(self, request, response):
        # type: (BaseMessage, BaseMessage) -> ExpectedObjConnection
        conn = ExpectedObjConnection(self)
        conn.in_obj = request
        conn.expected_obj = response
        return conn

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
        self.db.session.add(node)
        self.db.session.commit()

    def setup_default_clouds(self):
        self.zadjii_home = Cloud('zadjii', 'home', self.ZADJII_HOME)
        self.zadjii_work = Cloud('zadjii', 'work', self.ZADJII_WORK)
        self.claire_home = Cloud('claire', 'home', self.CLAIRE_HOME)
        self.db.session.add(self.zadjii_home)
        self.db.session.add(self.zadjii_work)
        self.db.session.add(self.claire_home)
        self.db.session.commit()

    def test_find_mirror_for_file(self):
        self.setup_default_clouds()

        c = self.controller._find_mirror_for_file('/user/home/zadjii/nebula/zadjii/home')
        self.assertNotEqual(None, c)
        self.assertEqual(self.zadjii_home.id, c.id)
        c = self.controller._find_mirror_for_file('/user/home/zadjii/nebula/zadjii/home/foo')
        self.assertNotEqual(None, c)
        self.assertEqual(self.zadjii_home.id, c.id)
        c = self.controller._find_mirror_for_file('/user/home/zadjii/nebula/zadjii/home/foo/bar')
        self.assertNotEqual(None, c)
        self.assertEqual(self.zadjii_home.id, c.id)
        c = self.controller._find_mirror_for_file('/user/home/zadjii/nebula/zadjii/work/foo/bar')
        self.assertNotEqual(None, c)
        self.assertEqual(self.zadjii_work.id, c.id)
        c = self.controller._find_mirror_for_file('/user/home/claire/nebula/claire/home/foo/bar')
        self.assertNotEqual(None, c)
        self.assertEqual(self.claire_home.id, c.id)

        c = self.controller._find_mirror_for_file('/user/home/')
        self.assertEqual(None, c)
        c = self.controller._find_mirror_for_file('/user/home/zadjii')
        self.assertEqual(None, c)
        c = self.controller._find_mirror_for_file('/user/home/zadjii/nebula')
        self.assertEqual(None, c)

    def test_create_file(self):
        self.setup_default_clouds()
        initial_modification_time = self.zadjii_home.last_modified()
        self.assertEqual(None, initial_modification_time)
        rd = self.controller.local_create_file(self.ZADJII_HOME + '/foo')
        self.assertEqual(True, rd.success)
        node = rd.data
        self.assertNotEqual(None, node)
        self.assertEqual(None, self.zadjii_home.last_sync())
        modified_0 = self.zadjii_home.last_modified()
        self.assertEqual(node.last_modified, modified_0)
        self.assertNotEqual(initial_modification_time, modified_0)

    def test_create_file_bad(self):
        self.setup_default_clouds()
        initial_modification_time = self.zadjii_home.last_modified()
        self.assertEqual(None, initial_modification_time)
        rd = self.controller.local_create_file(self.ZADJII_HOME + '/../foo')
        self.assertEqual(False, rd.success)
        node = rd.data
        self.assertEqual(None, node)
        self.assertEqual(None, self.zadjii_home.last_sync())
        self.assertEqual(initial_modification_time, self.zadjii_home.last_modified())

    def test_create_files_deep(self):
        self.setup_default_clouds()
        initial_modification_time = self.zadjii_home.last_modified()
        self.assertEqual(None, initial_modification_time)
        rd = self.controller.local_create_file(self.ZADJII_HOME + '/foo/bar/baz')
        self.assertEqual(True, rd.success)
        node = rd.data
        self.assertNotEqual(None, node)
        self.assertEqual(None, self.zadjii_home.last_sync())
        modified_0 = self.zadjii_home.last_modified()
        self.assertEqual(node.last_modified, modified_0)
        self.assertNotEqual(initial_modification_time, modified_0)
        self.assertEqual(node.id, 3)
        self.assertEqual(self.db.session.query(FileNode).count(), 3)

        rd = self.controller.local_create_file(self.ZADJII_HOME + '/foo/bar/baz/bingo/bango/bongo')
        self.assertEqual(True, rd.success)
        node2 = rd.data
        self.assertNotEqual(None, node2)
        self.assertEqual(None, self.zadjii_home.last_sync())
        modified_1 = self.zadjii_home.last_modified()
        self.assertEqual(node2.last_modified, modified_1)
        self.assertNotEqual(initial_modification_time, modified_1)
        self.assertNotEqual(modified_1, modified_0)
        self.assertEqual(node2.id, 6)
        self.assertEqual(self.db.session.query(FileNode).count(), 6)

    def test_modify_files_deep(self):
        self.setup_default_clouds()
        initial_modification_time = self.zadjii_home.last_modified()
        self.assertEqual(None, initial_modification_time)
        rd = self.controller.local_create_file(self.ZADJII_HOME + '/foo/bar/baz')
        self.assertEqual(True, rd.success)
        node = rd.data
        self.assertNotEqual(None, node)
        self.assertEqual(None, self.zadjii_home.last_sync())
        modified_0 = self.zadjii_home.last_modified()
        self.assertEqual(node.last_modified, modified_0)
        self.assertNotEqual(initial_modification_time, modified_0)
        self.assertEqual(node.id, 3)
        self.assertEqual(self.db.session.query(FileNode).count(), 3)

        sync_0 = datetime.utcnow()
        node.sync(sync_0)
        self.assertEqual(sync_0, self.zadjii_home.last_sync())
        self.assertLess(modified_0, sync_0)
        unsynced = self.zadjii_home.modified_since_last_sync()
        self.assertEqual(2, len(unsynced))

        rd, bar_path = RelativePath.make_relative('foo/bar')
        self.assertTrue(rd.success)
        node_bar = self.zadjii_home.get_child_node(bar_path)
        bar_creation = node_bar.created_on
        self.assertNotEqual(None, bar_creation)
        self.assertGreater(sync_0, bar_creation)
        bar_modified_0 = datetime.utcnow()
        self.assertLess(modified_0, bar_modified_0)
        self.assertLess(sync_0, bar_modified_0)
        self.controller.local_modify_file(self.ZADJII_HOME + '/foo/bar', timestamp=bar_modified_0)
        self.assertEqual(bar_modified_0, node_bar.last_modified)
        self.assertEqual(bar_modified_0, self.zadjii_home.last_modified())
        self.assertEqual(sync_0, self.zadjii_home.last_sync())
        

def main():
    unittest.main()


if __name__ == '__main__':
    main()
