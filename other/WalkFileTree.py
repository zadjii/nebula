__author__ = 'Mike'

import os
import sys
from stat import *

default_path = 'C:\\tmp'


def walktree(top, callback):
    """recursively descend the directory tree rooted at top,
       calling the callback function for each regular file"""

    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        mode = os.stat(pathname).st_mode
        if S_ISDIR(mode):
            # It's a directory, recurse into it
            walktree(pathname, callback)
        elif S_ISREG(mode):
            # It's a file, call the callback function
            callback(pathname)
        else:
            # Unknown file type, print a message
            print 'Skipping %s' % pathname


def visit_file(filename):
    print 'visiting', filename

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else default_path
    walktree(path, visit_file)