import logging
import os
import unittest
from .HostDbTestBase import *


class HostMirrorTests(HostDbTestBase):
    def test_ctor(self):
        cloud = Cloud('zadjii', 'home', '~')
        self.db.session.add(cloud)
        self.db.session.commit()
        self.assertEqual(cloud.id, 1)

    # def test_foo(self):
    #     self.assertFalse(True)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
