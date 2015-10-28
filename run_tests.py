from subprocess import Popen

from test.repop_dbs import repop_dbs

__author__ = 'zadjii'
from test import test_msgs, test_client_setup, test_msgs_2

if __name__ == '__main__':

    repop_dbs()
    test_msgs.test_msgs()
    print '#' * 80
    test_msgs_2.test_msgs()
    print '#' * 80
    test_client_setup.client_setup_test()
    print '#' * 80


