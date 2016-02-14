import os
import shutil
from subprocess import Popen

__author__ = 'Mike'


def repop_dbs():
    # print os.curdir
    # print os.listdir(os.curdir)
    if os.name == 'nt':
        reset_dbs = Popen('reset_dbs.bat')
    else:
        reset_dbs = Popen('bash ./reset_dbs.sh', shell=True)
    reset_dbs.wait()
    print '#' * 80

    autopop = Popen('python db_autopopulate_000.py', shell=True)
    autopop.wait()
    print '# DBs repop\'d'
    print '#' * 80

    # if os.path.exists('test_out'):
    #     shutil.rmtree('test_out', ignore_errors=True)
    if not os.path.exists('test_out'):
        os.makedirs('test_out')
    if not os.path.exists('test_out/tmp0'):
        os.makedirs('test_out/tmp0')
    if not os.path.exists('test_out/tmp1'):
        os.makedirs('test_out/tmp1')
    if not os.path.exists('test_out/tmp2'):
        os.makedirs('test_out/tmp2')
    if not os.path.exists('test_out/tmp3'):
        os.makedirs('test_out/tmp3')
    if not os.path.exists('test_out/tmp4'):
        os.makedirs('test_out/tmp4')

