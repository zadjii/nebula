import logging
import os
import unittest
from common_util import RelativePath, get_path_elements


class RelativePathTests(unittest.TestCase):

    def test_easy(self):
        rp = RelativePath()
        rd = rp.from_relative('foo')
        self.assertTrue(rd.success)
        self.assertEqual('foo', rp.to_string())

        rd = rp.from_relative('./bar')
        self.assertTrue(rd.success)
        self.assertEqual('bar', rp.to_string())

        rd = rp.from_relative('/baz')
        self.assertTrue(rd.success)
        self.assertEqual('baz', rp.to_string())

    def test_roots(self):
        rp = RelativePath()
        rd = rp.from_relative('/')
        self.assertTrue(rd.success)
        self.assertEqual('.', rp.to_string())

        rd = rp.from_relative('./')
        self.assertTrue(rd.success)
        self.assertEqual('.', rp.to_string())

        rd = rp.from_relative('.')
        self.assertTrue(rd.success)
        self.assertEqual('.', rp.to_string())

    def test_windows(self):
        rp = RelativePath()
        rd = rp.from_relative('foo\\bar')
        self.assertTrue(rd.success)
        self.assertEqual('foo/bar', rp.to_string())

        rd = rp.from_relative('.\\bar')
        self.assertTrue(rd.success)
        self.assertEqual('bar', rp.to_string())

        rd = rp.from_relative('c:\\baz')
        self.assertTrue(rd.success)
        self.assertEqual('baz', rp.to_string())

        rd = rp.from_relative('\\\\scratch')
        self.assertFalse(rd.success)
        # TODO: Should this be an exception
        # self.assertEqual('scratch', rp.to_string())

    def test_parents(self):
        rp = RelativePath()
        rd = rp.from_relative('foo/../bar')
        self.assertTrue(rd.success)
        self.assertEqual('bar', rp.to_string())

        rd = rp.from_relative('bar/../../baz')
        self.assertTrue(rd.success)
        self.assertEqual('baz', rp.to_string())

        rd = rp.from_relative('/baz/../../foo')
        self.assertTrue(rd.success)
        self.assertEqual('foo', rp.to_string())

        rd = rp.from_relative('/baz/../../foo/../hello')
        self.assertTrue(rd.success)
        self.assertEqual('hello', rp.to_string())

    def test_elements(self):
        rp = RelativePath()
        rd = rp.from_relative('foo/bar')
        self.assertTrue(rd.success)
        dirs = get_path_elements(rp.to_string())
        self.assertEqual(['foo', 'bar'], dirs)

        rd = rp.from_relative('./baz/bar')
        self.assertTrue(rd.success)
        dirs = rp.to_elements()
        self.assertEqual(['baz', 'bar'], dirs)

        rd = rp.from_relative('foo/bar')
        self.assertTrue(rd.success)
        dirs = rp.to_elements()
        self.assertEqual(['foo', 'bar'], dirs)

        rd = rp.from_relative('/bingo/bango/bongo')
        self.assertTrue(rd.success)
        dirs = rp.to_elements()
        self.assertEqual(['bingo', 'bango', 'bongo'], dirs)

        rd = rp.from_relative('.\\foo\\bar\\baz')
        self.assertTrue(rd.success)
        dirs = rp.to_elements()
        self.assertEqual(['foo', 'bar', 'baz'], dirs)

    def test_from_absolute_basic(self):
        rp = RelativePath()
        rd = rp.from_absolute('/mnt/c/Users/mike/', '/mnt/c/Users/mike/docs')
        self.assertTrue(rd.success)
        self.assertEqual('docs', rp.to_string())

        rd = rp.from_absolute('/mnt/c/Users/mike/', '/mnt/c/Users/mike/docs/foo/bar')
        self.assertTrue(rd.success)
        self.assertEqual('docs/foo/bar', rp.to_string())

        rd = rp.from_absolute('/mnt/c/Users/mike/', '/mnt/c/Users/mike/docs/foo/bar/../..')
        self.assertTrue(rd.success)
        self.assertEqual('docs', rp.to_string())

        rd = rp.from_absolute('/mnt/c/Users/mike/', '/mnt/c/Users/claire/docs/')
        self.assertFalse(rd.success)

        rd = rp.from_absolute('/mnt/c/Users/mike/', '/mnt/c/Users/mike/../claire')
        self.assertFalse(rd.success)

        # TODO: This should fail
        rd = rp.from_absolute('/mnt/c/Users/mike/', '/mnt/c/Users/claire/../mike/docs')
        self.assertTrue(rd.success)



def main():
    unittest.main()

if __name__ == '__main__':
    main()
