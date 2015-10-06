import os
import shutil
from subprocess import Popen

__author__ = 'Mike'
reset_dbs = Popen('reset_dbs.bat')


def repop_dbs():
    global reset_dbs
    if os.name == 'nt':
        pass
    else:
        reset_dbs = Popen('sh reset_dbs.sh')
    reset_dbs.wait()
    print '#' * 80

    autopop = Popen('python db_autopopulate_000.py')
    autopop.wait()
    print '# DBs repop\'d'
    print '#' * 80

    if os.path.exists('test_out'):
        shutil.rmtree('test_out', ignore_errors=True)
    os.makedirs('test_out')
    os.makedirs('test_out/tmp0')
    os.makedirs('test_out/tmp1')
    os.makedirs('test_out/tmp2')
    os.makedirs('test_out/tmp3')
    os.makedirs('test_out/tmp4')
