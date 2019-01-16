import logging
import os
import unittest

from common.Instance import Instance
from common_util import get_path_elements, get_log_path, get_log_verbosity
from common.RelativePath import RelativePath
from host.NebsInstance import NebsInstance


class CommandLineTests(unittest.TestCase):

    def test_easy(self):
        argv = 'nebs.py -i foo'.split(' ')
        self.assertEqual(argv, ['nebs.py', '-i', 'foo'])
        working_dir, argv = Instance.get_working_dir(argv, is_remote=False)
        self.assertEqual(argv, ['nebs.py'])
        self.assertEqual(working_dir.split('/').pop(), 'foo')

    def test_with_things_after(self):
        argv = 'nebs.py -i foo start'.split(' ')
        self.assertEqual(argv, ['nebs.py', '-i', 'foo', 'start'])
        working_dir, argv = Instance.get_working_dir(argv, is_remote=False)
        self.assertEqual(argv, ['nebs.py', 'start'])
        log_path, argv = get_log_path(argv)
        self.assertEqual(argv, ['nebs.py', 'start'])
        log_level, argv = get_log_verbosity(argv)
        self.assertEqual(argv, ['nebs.py', 'start'])
        self.assertEqual(working_dir.split('/').pop(), 'foo')
        self.assertEqual(log_path, None)
        self.assertEqual(log_level, logging.INFO)

    def test_logging_with_things_after(self):
        argv = 'nebs.py -l /var/log/nebs.log start'.split(' ')
        self.assertEqual(argv, ['nebs.py', '-l', '/var/log/nebs.log', 'start'])
        working_dir, argv = Instance.get_working_dir(argv, is_remote=False)
        self.assertEqual(argv, ['nebs.py', '-l', '/var/log/nebs.log', 'start'])
        log_path, argv = get_log_path(argv)
        self.assertEqual(argv, ['nebs.py', 'start'])
        log_level, argv = get_log_verbosity(argv)
        self.assertEqual(argv, ['nebs.py', 'start'])
        # self.assertEqual(working_dir.split('/').pop(), 'foo')
        self.assertEqual(log_path, '/var/log/nebs.log')
        self.assertEqual(log_level, logging.INFO)

    def test_logging_with_verbosity(self):
        argv = 'nebs.py -l /var/log/nebs.log -v debug start'.split(' ')
        self.assertEqual(argv, ['nebs.py', '-l', '/var/log/nebs.log', '-v', 'debug', 'start'])
        working_dir, argv = Instance.get_working_dir(argv, is_remote=False)
        self.assertEqual(argv, ['nebs.py', '-l', '/var/log/nebs.log', '-v', 'debug', 'start'])
        log_path, argv = get_log_path(argv)
        self.assertEqual(argv, ['nebs.py', '-v', 'debug', 'start'])
        log_level, argv = get_log_verbosity(argv)
        self.assertEqual(argv, ['nebs.py', 'start'])
        # self.assertEqual(working_dir.split('/').pop(), 'foo')
        self.assertEqual(log_path, '/var/log/nebs.log')
        self.assertEqual(log_level, logging.DEBUG)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
