from subprocess import Popen, call
from time import sleep

__author__ = 'zadjii'
from test import test_msgs, client_setup

if __name__ == '__main__':

    reset_dbs = Popen('reset_dbs.bat')
    reset_dbs.wait()
    print '#' * 80
    autopop = Popen('python db_autopopulate_000.py')
    autopop.wait()
    print '#' * 80
    sleep(2)
    test_msgs.test_msgs()
    print '#' * 80
    client_setup.client_setup()