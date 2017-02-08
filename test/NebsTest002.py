import os
import unittest

from test.util import start_nebs_and_nebr


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)


if __name__ == '__main__':

    os.environ['NEBULA_LOCAL_DEBUG'] = '1'
    global host_0, host_1, remote
    try:
        host_0, host_1, remote = start_nebs_and_nebr(test_root)
        print '\x1b[30;42m##### Nebula processes started #####\x1b[0m'
    except Exception, e:
        teardown_children([host_0, remote])
        raise e

    unittest.main()
