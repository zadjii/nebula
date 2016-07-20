from subprocess import Popen
from time import sleep

from test.all_dbs_repop import repop_dbs

__author__ = 'zadjii'
from test import test_msgs, test_client_setup, test_msgs_2, test_nebs

if __name__ == '__main__':

    repop_dbs()
    # test_msgs.test_msgs()
    # print '#' * 80
    # test_msgs_2.test_msgs()
    test_nebs.basic_test()

    print '#' * 80
    repop_dbs()
    # test_client_setup.client_setup_test()
    # god this test is broken ass shit.
    print '#' * 80


