import logging
import os
from datetime import timedelta
import unittest
from .HostDbTestBase import HostDbTestBase
from host.models.Remote import *
from host.models.Cloud import *
from host.models.FileNode import *


class HostMirrorTests(HostDbTestBase):

    def test_ctor(self):
        cloud = Cloud('zadjii', 'home', '~/nebulas/zadjii/home')
        self.db.session.add(cloud)
        self.db.session.commit()
        self.assertEqual(cloud.id, 1)
        self.assertEqual(cloud.full_name(), 'zadjii/home')
        self.assertEqual(cloud.root_directory, '~/nebulas/zadjii/home')
        self.assertEqual(len(cloud.all_children()), 0)


    def test_make_tree_to_root(self):
        cloud = Cloud('zadjii', 'home', '~/nebulas/zadjii/home')
        self.db.session.add(cloud)
        self.db.session.commit()
        self.assertEqual(cloud.id, 1)
        self.assertEqual(cloud.full_name(), 'zadjii/home')
        self.assertEqual(cloud.root_directory, '~/nebulas/zadjii/home')
        self.assertEqual(len(cloud.all_children()), 0)

        rp = RelativePath()
        rp.from_relative('./one')
        filenode = cloud.make_tree(rp, self.db)
        self.assertTrue(filenode is not None)
        self.db.session.commit()
        self.assertEqual(len(cloud.all_children()), 1)
        self.assertEqual(filenode.cloud_id, cloud.id)
        self.assertEqual(filenode.relative_path().to_string(), 'one')
        self.assertFalse(filenode.is_root())
        self.assertTrue(cloud.is_root())

        rp.from_relative('./oneB')
        filenode = cloud.make_tree(rp, self.db)
        self.assertTrue(filenode is not None)
        self.db.session.commit()
        self.assertEqual(len(cloud.all_children()), 2)
        self.assertEqual(filenode.cloud_id, cloud.id)
        self.assertEqual(filenode.relative_path().to_string(), 'oneB')
        self.assertFalse(filenode.is_root())

    def test_make_tree_deep_nodes(self):
        cloud = Cloud('zadjii', 'home', '~/nebulas/zadjii/home')
        self.db.session.add(cloud)
        self.db.session.commit()
        self.assertEqual(cloud.id, 1)
        self.assertEqual(cloud.full_name(), 'zadjii/home')
        self.assertEqual(cloud.root_directory, '~/nebulas/zadjii/home')
        self.assertEqual(len(cloud.all_children()), 0)

        rp = RelativePath()
        rp.from_relative('./one')
        filenode = cloud.make_tree(rp, self.db)
        self.assertTrue(filenode is not None)
        self.db.session.commit()
        self.assertEqual(len(cloud.all_children()), 1)
        self.assertEqual(filenode.cloud_id, cloud.id)
        self.assertEqual(filenode.relative_path().to_string(), 'one')
        self.assertFalse(filenode.is_root())
        self.assertTrue(cloud.is_root())
        self.assertEqual(filenode.parent, None)

        rp.from_relative('./one/two')
        filenode = cloud.make_tree(rp, self.db)
        self.assertTrue(filenode is not None)
        self.db.session.commit()
        self.assertEqual(len(cloud.all_children()), 1)
        self.assertEqual(filenode.cloud_id, None)
        self.assertEqual(filenode.relative_path().to_string(), 'one/two')
        self.assertFalse(filenode.is_root())
        self.assertTrue(cloud.is_root())
        self.assertEqual(filenode.parent.id, 1)
        self.assertEqual(filenode.parent.relative_path().to_string(), 'one')

        rp.from_relative('./one/two/three/four/five')
        filenode = cloud.make_tree(rp, self.db)
        self.assertTrue(filenode is not None)
        self.db.session.commit()
        self.assertEqual(len(cloud.all_children()), 1)
        self.assertEqual(filenode.cloud_id, None)
        self.assertEqual(filenode.relative_path().to_string(), 'one/two/three/four/five')
        self.assertFalse(filenode.is_root())
        self.assertTrue(cloud.is_root())
        self.assertEqual(filenode.parent.relative_path().to_string(),
                         'one/two/three/four')
        self.assertEqual(filenode.parent.parent.relative_path().to_string(),
                         'one/two/three')
        self.assertEqual(filenode.parent.parent.parent.relative_path().to_string(),
                         'one/two')
        self.assertEqual(filenode.parent.parent.parent.parent.relative_path().to_string(),
                         'one')

    def test_last_modified(self):
        cloud = Cloud('zadjii', 'home', '~/nebulas/zadjii/home')
        self.db.session.add(cloud)
        self.db.session.commit()

        self.assertEqual(None, cloud.last_modified())

        rp = RelativePath()
        rp.from_relative('./one')
        one = cloud.make_tree(rp, self.db)
        self.assertEqual(one.created_on, cloud.last_modified())

        rp.from_relative('./one/two')
        two = cloud.make_tree(rp, self.db)
        self.assertTrue(one is not None)
        self.assertTrue(two is not None)
        self.db.session.commit()

        self.assertEqual(two.created_on, cloud.last_modified())

        timestamp_one = datetime.utcnow()
        timestamp_two = timestamp_one + timedelta(minutes=1)
        timestamp_three = timestamp_two + timedelta(minutes=1)
        one.modify(timestamp_one)
        two.modify(timestamp_one)
        self.db.session.commit()
        self.assertEqual(timestamp_one, cloud.last_modified())

        two.modify(timestamp_two)
        self.db.session.commit()
        self.assertEqual(timestamp_two, cloud.last_modified())

        one.modify(timestamp_three)
        self.db.session.commit()
        self.assertEqual(timestamp_three, cloud.last_modified())

    def test_last_sync_simple(self):
            cloud = Cloud('zadjii', 'home', '~/nebulas/zadjii/home')
            self.db.session.add(cloud)
            self.db.session.commit()

            self.assertEqual(None, cloud.last_sync())

            rp = RelativePath()
            rp.from_relative('./one')
            one = cloud.make_tree(rp, self.db)
            self.assertEqual(None, cloud.last_sync())

            rp.from_relative('./one/two')
            two = cloud.make_tree(rp, self.db)
            self.assertTrue(one is not None)
            self.assertTrue(two is not None)
            self.db.session.commit()

            self.assertEqual(None, cloud.last_sync())
            self.assertTrue(one.unsynced())
            self.assertTrue(two.unsynced())

            timestamp_zero = datetime.utcnow()
            timestamp_one = timestamp_zero + timedelta(minutes=1)
            timestamp_two = timestamp_one + timedelta(minutes=1)
            timestamp_three = timestamp_two + timedelta(minutes=1)

            one.sync(timestamp_one)
            self.db.session.commit()
            self.assertEqual(timestamp_one, cloud.last_sync())

            two.sync(timestamp_two)
            self.db.session.commit()
            self.assertEqual(timestamp_two, cloud.last_sync())

            one.sync(timestamp_three)
            self.db.session.commit()
            self.assertEqual(timestamp_three, cloud.last_sync())

    def test_last_sync_and_modify(self):
            cloud = Cloud('zadjii', 'home', '~/nebulas/zadjii/home')
            self.db.session.add(cloud)
            self.db.session.commit()

            self.assertEqual(None, cloud.last_sync())

            rp = RelativePath()
            rp.from_relative('./one')
            one = cloud.make_tree(rp, self.db)
            self.assertEqual(None, cloud.last_sync())

            rp.from_relative('./one/two')
            two = cloud.make_tree(rp, self.db)
            self.assertTrue(one is not None)
            self.assertTrue(two is not None)
            self.db.session.commit()

            self.assertEqual(None, cloud.last_sync())
            self.assertTrue(one.unsynced())
            self.assertTrue(two.unsynced())

            timestamp_zero = datetime.utcnow()
            timestamp_one = timestamp_zero + timedelta(minutes=1)
            timestamp_two = timestamp_one + timedelta(minutes=1)
            timestamp_three = timestamp_two + timedelta(minutes=1)
            timestamp_four = timestamp_three + timedelta(minutes=1)

            one.modify(timestamp_one)
            self.db.session.commit()
            self.assertEqual(timestamp_one, cloud.last_modified())
            self.assertEqual(None, cloud.last_sync())

            one.sync(timestamp_one)
            self.db.session.commit()
            self.assertEqual(timestamp_one, cloud.last_modified())
            self.assertEqual(timestamp_one, cloud.last_sync())

            two.modify(timestamp_two)
            self.db.session.commit()
            self.assertEqual(timestamp_two, cloud.last_modified())
            self.assertEqual(timestamp_one, cloud.last_sync())

            one.modify(timestamp_three)
            self.db.session.commit()
            self.assertEqual(timestamp_three, cloud.last_modified())
            self.assertEqual(timestamp_one, cloud.last_sync())

            two.sync(timestamp_two)
            self.assertEqual(timestamp_three, cloud.last_modified())
            self.assertEqual(timestamp_two, cloud.last_sync())

            two.modify(timestamp_three)
            one.sync(timestamp_four)
            self.assertEqual(timestamp_three, cloud.last_modified())
            self.assertEqual(timestamp_four, cloud.last_sync())

    def test_get_modified_since_last_sync(self):
        cloud = Cloud('zadjii', 'home', '~/nebulas/zadjii/home')
        self.db.session.add(cloud)
        self.db.session.commit()

        self.assertEqual(None, cloud.last_sync())

        rp = RelativePath()
        rp.from_relative('./one')
        one = cloud.make_tree(rp, self.db)
        self.assertEqual(None, cloud.last_sync())
        modified = cloud.modified_since_last_sync()
        self.assertEqual(1, len(modified))
        self.assertEqual(one.id, modified[0].id)

        rp.from_relative('./one/two')
        two = cloud.make_tree(rp, self.db)
        self.assertTrue(one is not None)
        self.assertTrue(two is not None)
        self.db.session.commit()
        modified = cloud.modified_since_last_sync()
        self.assertEqual(2, len(modified))
        self.assertEqual(two.id, modified[0].id)
        self.assertEqual(one.id, modified[1].id)

        self.assertEqual(None, cloud.last_sync())
        self.assertTrue(one.unsynced())
        self.assertTrue(two.unsynced())

        timestamp_zero = datetime.utcnow()
        timestamp_one = timestamp_zero + timedelta(minutes=1)
        timestamp_two = timestamp_one + timedelta(minutes=1)
        timestamp_three = timestamp_two + timedelta(minutes=1)
        timestamp_four = timestamp_three + timedelta(minutes=1)

        one.sync(timestamp_zero)
        modified = cloud.modified_since_last_sync()
        self.assertEqual(1, len(modified))
        self.assertEqual(two.id, modified[0].id)
        two.sync(timestamp_zero)
        modified = cloud.modified_since_last_sync()
        self.assertEqual(0, len(modified))

        one.modify(timestamp_one)
        self.db.session.commit()
        modified = cloud.modified_since_last_sync()
        self.assertEqual(1, len(modified))
        self.assertEqual(one.id, modified[0].id)
        self.assertEqual(timestamp_one, cloud.last_modified())
        self.assertEqual(timestamp_zero, cloud.last_sync())

        one.sync(timestamp_one)
        self.db.session.commit()
        modified = cloud.modified_since_last_sync()
        self.assertEqual(timestamp_one, cloud.last_modified())
        self.assertEqual(timestamp_one, cloud.last_sync())
        modified = cloud.modified_since_last_sync()
        self.assertEqual(0, len(modified))

        two.modify(timestamp_two)
        self.db.session.commit()
        modified = cloud.modified_since_last_sync()
        self.assertEqual(timestamp_two, cloud.last_modified())
        self.assertEqual(timestamp_one, cloud.last_sync())
        self.assertEqual(1, len(modified))
        self.assertEqual(two.id, modified[0].id)

        one.modify(timestamp_three)
        self.db.session.commit()
        modified = cloud.modified_since_last_sync()
        self.assertEqual(timestamp_three, cloud.last_modified())
        self.assertEqual(timestamp_one, cloud.last_sync())
        self.assertEqual(2, len(modified))
        # The ordering doesn't matter here - if this test breaks due to a
        #   change in the implementation of modified_since_last_sync, then
        #   fix the test
        self.assertEqual(two.id, modified[0].id)
        self.assertEqual(one.id, modified[1].id)

        two.sync(timestamp_two)
        modified = cloud.modified_since_last_sync()
        self.assertEqual(timestamp_three, cloud.last_modified())
        self.assertEqual(timestamp_two, cloud.last_sync())
        self.assertEqual(1, len(modified))
        self.assertEqual(one.id, modified[0].id)

        two.modify(timestamp_three)
        one.sync(timestamp_four)
        modified = cloud.modified_since_last_sync()
        self.assertEqual(timestamp_three, cloud.last_modified())
        self.assertEqual(timestamp_four, cloud.last_sync())
        self.assertEqual(1, len(modified))
        self.assertEqual(two.id, modified[0].id)

def main():
    unittest.main()


if __name__ == '__main__':
    main()
