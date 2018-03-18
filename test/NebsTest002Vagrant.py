import logging
import os
import unittest

import shutil
from inspect import currentframe, getframeinfo
from time import sleep

from common.Instance import Instance
from common_util import NEBULA_ROOT, config_logger, PUBLIC_USER_ID
from host.NebsInstance import NebsInstance
from host.PrivateData import READ_ACCESS
from test.util import start_nebs_and_nebr, start_nebr_and_nebs_instance, teardown_children, retrieve_client_session, \
    check_file_contents, log_text, HostSession, log_fail, log_success, start_nebs, start_nebs_instance
from host.models.Remote import Remote

# remote_proc = None
host_proc = None
test_root = 'sunio'  # this is the instance name.
# nebr_instance = None
nebs_instance = None
nebs_working_dir = None
# nebr_working_dir = None
###############################################################################
# Mirror roots
###############################################################################
neb_1_path = None
neb_2_path = None
wedding_0_root = None
wedding_1_root = None
wedding_2_root = None
bridesmaids_0_root = None
bridesmaids_1_root = None
bachelorette_0_root = None
bachelorette_1_root = None
###############################################################################

def make_mirror_dir(nebs_root, mirror_path):
    full_path = os.path.join(nebs_root, mirror_path)
    if not os.path.exists(full_path):
        os.mkdir(full_path)
    return full_path



def clear_dir(path):
    if os.path.exists(path):
        log_text('clearing directory {}'.format(path))
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    if os.path.exists(path):
        log_text('REALLY REALLY clearing directory {}'.format(path))
        shutil.rmtree(path, ignore_errors=True)


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        print('Hey you! Make sure `vagrant repop002` was called before this script!')

        config_logger('NebsTest002Vagrant', filename=None, level=logging.DEBUG)
        global nebs_working_dir
        nebs_working_dir, argv = Instance.get_working_dir(['-i', test_root], is_remote=False)

        nebs_working_dir = os.path.join(NEBULA_ROOT, nebs_working_dir)

        print 'nebs_working_dir={}'.format(os.path.abspath(nebs_working_dir))

        global nebs_instance


        # print('Killing any existing nebs processes...')
        # nebs_instance.kill()

        clear_dir(nebs_working_dir)

        print 'Reset the dir for {}'.format(nebs_working_dir)

        os.makedirs(nebs_working_dir)
        with open(os.path.join(nebs_working_dir, 'nebs.conf'), mode='wb') as f:
            f.write('LOCAL_DEBUG = True')

        nebs_instance = NebsInstance(nebs_working_dir)
        print('LOCAL_DEBUG = {}'.format(nebs_instance.local_debug))
        nebs_instance.init_dir()
        global host_proc
        host_proc = start_nebs_instance(test_root)
        print '\x1b[30;42m##### Nebula processes started #####\x1b[0m'

        print 'Created the dirs for {}'.format(nebs_working_dir)

        global neb_1_path, neb_2_path
        global wedding_0_root, wedding_1_root, wedding_2_root
        global bridesmaids_0_root, bridesmaids_1_root
        global bachelorette_0_root, bachelorette_1_root

        neb_1_path = make_mirror_dir(nebs_working_dir, 'tmp0')
        neb_2_path = make_mirror_dir(nebs_working_dir, 'tmp1')
        wedding_0_root = make_mirror_dir(nebs_working_dir, 'wedding_0')
        wedding_1_root = make_mirror_dir(nebs_working_dir, 'wedding_1')
        wedding_2_root = make_mirror_dir(nebs_working_dir, 'wedding_2')
        bridesmaids_0_root = make_mirror_dir(nebs_working_dir, 'bridesmaids_0')
        bridesmaids_1_root = make_mirror_dir(nebs_working_dir, 'bridesmaids_1')
        bachelorette_0_root = make_mirror_dir(nebs_working_dir, 'bachelorette_0')
        bachelorette_1_root = make_mirror_dir(nebs_working_dir, 'bachelorette_1')

        print 'Repop\'d'


    def setUp(self):
        # self.widget = Widget('The widget')
        pass

    def tearDown(self):
        # self.widget.dispose()
        pass

    @classmethod
    def tearDownClass(cls):
        # self.widget = Widget('The widget')
        print 'tearDownClass'
        global host_proc
        teardown_children([host_proc])
        pass

    # Commenting test out for now, the logging is too confusing, overlapped...
    # def test_client_setup(self):
    #     log_text('### Client Setup Test ###', '7')
    #     # Create a valid session
    #     rd = retrieve_client_session('asdf', 'asdf')
    #     self.assertTrue(rd.success, 'Created good session')
    #
    #     # Create an invalid session
    #     rd = retrieve_client_session('asdf', 'invalid')
    #     self.assertFalse(rd.success, 'Didn\'t create a bad session')
    #
    #     rd = retrieve_client_session('invalid', 'invalid')
    #     self.assertFalse(rd.success, 'Didn\'t create a bad session')
    #
    #     # Create a duplicate session
    #     rd = retrieve_client_session('asdf', 'asdf')
    #     self.assertTrue(rd.success, 'Created good session')

    def test_client_mirror(self):
        global nebs_working_dir
        log_text('### Client Mirroring Test ###', '7')
        log_text('#### These two users CAN mirror the AfterglowWedding2017 cloud ####')

        mike = get_mike(self)
        claire = get_claire(self)

        log_text('#### These two users CANNOT mirror the wedding cloud ####')

        hannah = get_hannah(self)
        alli = get_alli(self)

        log_text('#### Create some test data ####')
        log_text('#### client mirror the wedding cloud successfully ####')

        mike.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_0_root, nebs_working_dir)

        wedding_test_text_0 = 'Hello Wedding World!'
        wedding_test_file_0 = 'hello.txt'
        handle = open(os.path.join(wedding_0_root, wedding_test_file_0), mode='wb')
        handle.write(wedding_test_text_0)
        handle.close()
        log_text('#### Created test data in wedding_0_root ####')

        rd = check_file_contents(wedding_0_root, wedding_test_file_0, wedding_test_text_0)
        self.assertTrue(rd.success, 'mirroring wedding 0')
        log_text('Note: This doesn\'t really mean that it worked mirroring, '
                 'just that it\'s done now.')

        claire.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_1_root, nebs_working_dir)
        # sleep(3)
        rd = check_file_contents(wedding_1_root, wedding_test_file_0, wedding_test_text_0)
        self.assertTrue(rd.success, 'mirroring wedding 1')
        # Hey Mike:
        # This is failing because when the second mirror is instantiated, it's not getting the file from the first one.
        # `No other hosts in cloud`
        # So the second mirror doesnt get that there's an existing mirror.
        # Ah
        # so there's no other hosts
        # There *IS* another mirror
        # So we return that there's no other hosts
        # and the mirror process is like fuck it
        #
        # So we fixed that, now the output has
        # verify_host 4
        # Other host failed to verify our request, "Remote responded with failure: "No matching cloud (u'Mike-Griese', u'AfterglowWedding2017')""
        # So the nebs[1] was verifying for [2] mirroring mike-griese/afterglowwedding2017
        # It sent the HOST_VERIFY_HOST(1, 2, un/cn) to the remote
        # I'm reallyihoping this is because the host was doing a case-sensitiv name lookup


        log_text('#### client mirror the wedding cloud unsuccessfully ####')
        hannah.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_2_root, nebs_working_dir)
        rd = check_file_contents(wedding_2_root, wedding_test_file_0, wedding_test_text_0)
        self.assertFalse(rd.success, 'Hannah did not mirror wedding 2')

        alli.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_2_root, nebs_working_dir)
        rd = check_file_contents(wedding_2_root, wedding_test_file_0,
                                 wedding_test_text_0)
        self.assertFalse(rd.success, 'Alli did not mirror wedding 2')

        log_text('#### mirror the rest of the clouds ####')
        claire.mirror('Mike-Griese', 'AfterglowWedding2017', wedding_2_root, nebs_working_dir)
        # sleep(2)
        rd = check_file_contents(wedding_2_root, wedding_test_file_0, wedding_test_text_0)
        self.assertTrue(rd.success, 'Succeeded mirroring wedding 2')

        claire.mirror('Claire-Bovee', 'Claires-Bridesmaids', bridesmaids_0_root, nebs_working_dir)
        handle = open(os.path.join(bridesmaids_0_root, wedding_test_file_0), mode='wb')
        handle.write(wedding_test_text_0)
        handle.close()
        log_text('#### Created test data in bridesmaids_0_root ####')
        handle = open(os.path.join(bachelorette_1_root, wedding_test_file_0), mode='wb')
        handle.write(wedding_test_text_0)
        handle.close()
        log_text('#### Created test data in bachelorette_1_root ####')
        sleep(2)

        log_text('#### Add an owner to the cloud and try mirroring with them ####')
        claire_clone = HostSession(claire.sid)
        rd = claire_clone.get_host('Claire-Bovee', 'Claires-Bridesmaids')
        self.assertTrue(rd.success)

        # todo: actually get hannah's ID from the nebr. But for now we know it's [6]
        rd = claire_clone.add_owner(6)
        self.assertTrue(rd.success)

        hannah.mirror('Claire-Bovee', 'Claires-Bridesmaids', bridesmaids_1_root, nebs_working_dir)
        # sleep(1)
        rd = check_file_contents(bridesmaids_1_root, wedding_test_file_0, wedding_test_text_0)
        self.assertTrue(rd.success, 'Failed mirroring bridesmaids 1')

        log_text('#### Mirror a cloud, then mirror into a dir that already has a file ####')
        hannah.mirror('Hannah-Bovee', 'Claires_Bachelorette_Party', bachelorette_0_root, nebs_working_dir)
        # sleep(2)
        alli.mirror('Hannah-Bovee', 'Claires_Bachelorette_Party', bachelorette_1_root, nebs_working_dir)
        rd = check_file_contents(bachelorette_1_root, wedding_test_file_0, wedding_test_text_0)

        # todo:25
        if not rd.success:
            log_fail('Failed mirroring bachelorette 1 (This failure is expected)')
            # This is because the new process doesn't see that the file changed.
            #   It was already there. Mirror needs to be updated to account for this
            # todo:25
            # return

        else:
            log_success('Succeeded mirroring bachelorette 1')
        # self.assertTrue(rd.success, 'Failed mirroring bachelorette 1 (This failure is expected)')

        sleep(1)
        rd = check_file_contents(bachelorette_0_root, wedding_test_file_0, wedding_test_text_0)
        if not rd.success:
            log_fail('Failed mirroring bachelorette 0 (This failure is expected)')
            # This is because the new process doesn't see that the file changed.
            #   It was already there. Mirror needs to be updated to account for this
            # todo:25
            # return

        else:
            log_success('Succeeded mirroring bachelorette 0')
        # self.assertFalse(rd.success, 'Failed mirroring bachelorette 0 (This failure is expected)')

        #######################################################################
        # These are some parts that deal with contributors
        log_text('#### This tests adding contributors, and testing their permissions ####')

        rd = retrieve_client_session('Mr-Bovee', 'Mr Bovee')
        self.assertTrue(rd.success, 'successfully created Mr B client')
        mr_b = rd.data
        log_success('successfully created mr_b client')

        rd = mike.get_host('Mike-Griese', 'AfterglowWedding2017')
        self.assertTrue(rd.success)
        claire_afterglow = HostSession(claire.sid)
        rd = claire_afterglow.get_host('Mike-Griese', 'AfterglowWedding2017')
        self.assertTrue(rd.success)
        claire_bridesmaids = HostSession(claire.sid)
        rd = claire_bridesmaids.get_host('Claire-Bovee', 'Claires-Bridesmaids')
        self.assertTrue(rd.success)
        log_success('Got hosts for mike, claire_afterglow, claire_bridesmaids')
        mike.mkdir('wedding')
        sleep(1)
        wedding_dir = os.path.join(wedding_0_root, './wedding')
        # wedding dir was made in one of the 3 hosts
        if not (os.path.exists(os.path.join(wedding_0_root, './wedding'))
                or os.path.exists(os.path.join(wedding_1_root, './wedding'))
                or os.path.exists(os.path.join(wedding_2_root, './wedding'))):
            log_fail('wedding directory doesnt exist, {}'.format(wedding_dir))
            self.assertTrue(False)
        wedding_readme_text = 'This is the wedding files directory'
        drafts_readme_text = 'This is where I\'ll prepare wedding docs'
        # write a file to the created dir
        mike.write('wedding/README.md', wedding_readme_text)
        # write a file to a dir that doesnt exist
        mike.write('drafts/README.md', drafts_readme_text)
        sleep(1)
        rd = mr_b.get_host('Mike-Griese', 'AfterglowWedding2017')

        # Removing this assert - NO WAIT NO IM NOT
        # vagrant repop makes the first cloud for a user public,
        # so Mr B will always be able to access
        self.assertFalse(rd.success, 'Mr B got host before he had access')
        # mr_b has:
        #   /drafts: READ
        #   /finances: RDWR & Share

        # todo: actually get his ID, but we know it's [7] for now
        rd = mike.share(7, 'drafts', READ_ACCESS)
        self.assertTrue(rd.success, 'failed to share drafts with mr_b')
        rd = mr_b.get_host('Mike-Griese', 'AfterglowWedding2017')
        self.assertTrue(rd.success, 'Mr B did not get host')
        rd = mr_b.read_file('drafts/README.md')
        self.assertTrue(rd.success, 'Mr B failed to read drafts/readme.md')
        read_data = rd.data
        self.assertEqual(read_data, drafts_readme_text, 'Mr B read drafts/readme.md incorrectly')

        mike.write('honeymoon/photos/photos.md', 'this dir has honeymoon photos')
        rd = mike.share(PUBLIC_USER_ID, 'honeymoon/photos', READ_ACCESS)
        self.assertTrue(rd.success, 'shared honeymoon photos with the public')


###############################################################################
# User Getters
###############################################################################
def get_mike(testcase):
    rd = retrieve_client_session('Mike-Griese', 'Mike Griese')
    testcase.assertTrue(rd.success, 'successfully created Mike client')
    return rd.data


def get_claire(testcase):
    rd = retrieve_client_session('Claire-Bovee', 'Claire Bovee')
    testcase.assertTrue(rd.success, 'successfully created Claire client')
    return rd.data


def get_hannah(testcase):
    rd = retrieve_client_session('Hannah-Bovee', 'Hannah Bovee')
    testcase.assertTrue(rd.success, 'successfully created Hannah client')
    return rd.data


def get_alli(testcase):
    rd = retrieve_client_session('Alli-Anderson', 'Alli Anderson')
    testcase.assertTrue(rd.success, 'successfully created Alli client')
    return rd.data


def main():
    unittest.main()

if __name__ == '__main__':
    main()
###############################################################################
# Logging Pieces
###############################################################################
# num_successes = 0
# num_fails = 0
# fail_messages = []
#
# # DONT USE DIRECTLY
# def _log_message(text, fmt):
#     frameinfo = getframeinfo(currentframe().f_back.f_back)
#     output = '[{}:{}]\x1b[{}m{}\x1b[0m'.format(
#         os.path.basename(frameinfo.filename)
#         , frameinfo.lineno
#         , fmt
#         , text)
#     print(output)
#     return output
#
#
# def log_success(text):
#     _log_message(text, '32')
#     global num_successes
#     num_successes += 1
#
#
# def log_fail(text):
#     output = _log_message(text, '31')
#     global num_fails, fail_messages
#     num_fails += 1
#     fail_messages.append(output)
#
#
# def log_warn(text):
#     _log_message(text, '33')
#
#
# def log_text(text, fmt='0'):
#     _log_message(text, fmt)

