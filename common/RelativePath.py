import os
import posixpath
from os import path

from common_util import Error, ResultAndData


class RelativePath(object):
    # Stores a relative path as a non-delimited string. Ex:
    # [0]   ./foo -> foo
    # [1]   /bar -> bar
    # [2]   who\goes\there -> who/goes/there
    # [3]   foo/../../what -> what
    # See RelativePathTests
    def __init__(self):
        self._path = None

    def from_relative(self, relative_path_string):
        """
        Use this to construct a RelativePath.
        This way, user input will be validated
        :param relative_path_string:
        :return:
        """
        working = relative_path_string
        if working == '':
            working = '/'

        if not os.path.isabs(working):
            working = os.path.join('/', working)
        try:
            working = os.path.relpath(working, os.path.normpath('/'))
        except ValueError as e:
            return Error(e.message)
        working = posixpath.normpath(working)

        working_elems = working.split('\\')

        working = '/'.join(working_elems)
        working = posixpath.normpath(working)
        self._path = working

        is_child = working == '.' or os.path.abspath(working).startswith(os.path.abspath('.')+os.sep)
        return ResultAndData(is_child, None)

    def from_absolute(self, root, full_path):
        # type: (str, str) -> ResultAndData
        dirpath = posixpath.normpath(root)
        childpath = posixpath.normpath(full_path)
        self._path = os.path.relpath(childpath, dirpath)
        rd = ResultAndData(childpath.startswith(dirpath), None)
        if rd.success:
            rd = self.from_relative(self._path)
        return rd


    @staticmethod
    def make_relative(relative_path_string):
        # type: (str) -> (ResultAndData, RelativePath)
        rp = RelativePath()
        rd = rp.from_relative(relative_path_string)
        return rd, rp

    def to_string(self):
        return self._path

    def to_absolute(self, root):
        return os.path.join(root, self._path)

    def to_elements(self):
        # type: () -> [str]
        working_path = self._path
        dirs = []
        while True:
            head, tail = os.path.split(working_path)
            if tail != '':
                dirs.append(tail)
            else:
                if head != '':
                    dirs.append(head)
                break
            working_path= head
        dirs.reverse()
        return dirs

    def to_elements_no_root(self):
        # type: () -> [str]
        dirs = self.to_elements()
        if len(dirs) > 0 and dirs[0] == '.':
            dirs.pop(0)
        return dirs

    def is_root(self):
        # type: () -> bool
        """
        Returns true if this RelativePath represents the root directory the path is relative to.
        """
        return self._path == '.'

