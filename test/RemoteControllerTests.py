import unittest
import time
from datetime import timedelta
from common_util import *
from connections.AbstractConnection import AbstractConnection
from messages import *
from msg_codes import *
from messages.BaseMessage import BaseMessage
from remote.models.Cloud import *
from remote.models.User import *
from remote.models.Host import *
from remote.RemoteController import RemoteController
from remote.NebrInstance import NebrInstance

from ExpectedObjConnection import ExpectedObjConnection

# You there copy-pasting this - make sure to add it to all_unit_tests.py as well!
class RemoteControllerTests(unittest.TestCase):
    def expectResponse(self, request, response):
        # type: (BaseMessage, BaseMessage) -> ExpectedObjConnection
        conn = ExpectedObjConnection(self)
        conn.in_obj = request
        conn.expected_obj = response
        return conn

    def setUp(self):
        self.instance = NebrInstance(working_dir=None, unittesting=True)
        self.instance.disable_ssl = True
        self.instance.get_db().create_all()
        self.db = self.instance.get_db()
        self.controller = RemoteController(self.instance)
        # This doesn't work - we'll need some other way to get logging from the
        # tests that failed.
        #
        # config_logger('RemoteControllerTests', None, logging.DEBUG)

    def tearDown(self):
        pass

    def test_ctor(self):
        self.assertNotEqual(None, self.controller)
        # Make sure that the controller's instance's DB is the same as what we created
        self.assertNotEqual(None, self.db)
        self.assertEqual('sqlite:///', self.controller.get_instance()._db_uri())
        self.assertEqual(self.db.Base.metadata.tables, self.controller.get_instance().get_db().Base.metadata.tables)
        self.assertEqual(self.db.Base.metadata, self.controller.get_instance().get_db().Base.metadata)

    def test_create_user(self):
        user = User()
        user.name = 'zadjii'
        self.db.session.add(user)
        self.db.session.commit()
        self.assertEqual(1, len(self.db.session.query(User).all()))

    def test_create_cloud(self):
        user = User()
        user.name = 'zadjii'
        self.db.session.add(user)
        cloud = Cloud(user)
        self.db.session.add(cloud)
        self.db.session.commit()
        self.assertEqual(1, len(self.db.session.query(Cloud).all()))

    def setup_default_clouds(self):
        self.zadjii = User()
        self.zadjii.name = 'zadjii'
        self.db.session.add(self.zadjii)

        # We're using a created time here that's definitely in the past, because
        # sometimes all this executes in under a millisecond, and then some
        # tests get confused, since the time resolution is only milliseconds
        created = datetime.utcnow() - timedelta(0, 1, 0)

        self.zadjii_home = Cloud(self.zadjii)
        self.zadjii_home.name = 'home'
        self.db.session.add(self.zadjii_home)
        self.zadjii_work = Cloud(self.zadjii)
        self.zadjii_work.name = 'work'
        self.db.session.add(self.zadjii_work)

        # set the cloud's created_on to the time in the past.
        self.zadjii_home.created_on = created
        self.zadjii_work.created_on = created

        self.host_0 = Host()
        self.host_1 = Host()
        self.db.session.add(self.host_0)
        self.db.session.add(self.host_1)
        self.db.session.commit()

        self.mirror_0 = Mirror(self.zadjii_home, self.host_0)
        self.db.session.add(self.mirror_0)
        self.mirror_1 = Mirror(self.zadjii_home, self.host_0)
        self.db.session.add(self.mirror_1)

        # Initialize the host, cloud with some sane defaults.
        # * mirror_0 is the most recently sync'd mirror, and it's active
        # * host_0 (on which mirror_0 is hosted) is also active
        now = datetime.utcnow()
        self.mirror_0.last_sync = now
        self.mirror_0.last_handshake = now
        self.mirror_0.completed_mirroring = True
        self.host_0.last_update = now

        # Additionally, make the mirror_1 active, but leave it's last_sync
        # unchanged. mirror_1.last_sync will be self.zadjii_home.created_on
        self.mirror_1.last_handshake = now
        self.mirror_1.completed_mirroring = True

        self.db.session.commit()

    def test_default_setup(self):
        self.setup_default_clouds()
        self.assertEqual(2, len(self.db.session.query(Cloud).all()))

    def test_filter_message_works(self):
        """
        This is just a canary test to make sure that we can test filtering messages like this
        """
        self.setup_default_clouds()
        req = HostMoveRequestMessage(INVALID_HOST_ID, '1::1', 'my_fake_cert_request')
        resp = HostMoveResponseMessage(3, None)
        conn = self.expectResponse(req, resp)
        self.controller.filter_func(conn, '')

    def test_mirror_handshake_error(self):
        """
        Make sure that when a host sends a MirrorHandshake with a last_sync
        greater than the cloud's last_sync, we reply with an error
        """
        self.setup_default_clouds()

        clouds_last_sync = self.zadjii_home.last_sync_time()
        later = clouds_last_sync + timedelta(1, 0, 0)

        req = MirrorHandshakeMessage(
            mirror_id=1,
            last_sync=datetime_to_string(later),
            last_modified=datetime_to_string(later),
            hostname='hostname',
            used_space=0,
            remaining_space=INFINITE_SIZE
        )

        resp = InvalidStateMessage('Mirror\'s last_sync was newer than the cloud\'s last_update')
        conn = self.expectResponse(req, resp)
        self.controller.filter_func(conn, '')


    def test_mirror_handshake_get_hosts(self):
        """
        Make sure that when a host sends a MirrorHandshake with a last_sync
        less than the cloud's last_update, we reply with hosts to sync with
        """
        self.setup_default_clouds()

        clouds_last_sync = self.zadjii_home.last_sync_time()
        earlier = clouds_last_sync - timedelta(1, 0, 0)

        req = MirrorHandshakeMessage(
            mirror_id=2,
            last_sync=datetime_to_string(earlier),
            last_modified=datetime_to_string(earlier),
            hostname='hostname',
            used_space=0,
            remaining_space=INFINITE_SIZE
        )

        resp = RemoteMirrorHandshakeMessage(id=2,
                                            new_sync=None,
                                            sync_end=datetime_to_string(clouds_last_sync),
                                            last_all_sync=None,
                                            hosts=[self.mirror_0.to_dict()])
        conn = self.expectResponse(req, resp)
        self.controller.filter_func(conn, '')

    def test_mirror_handshake_get_hosts_with_none_sync_time(self):
        """
        Make sure that when a host sends a MirrorHandshake with a
        last_sync=None, we reply with hosts to sync with
        """
        self.setup_default_clouds()

        clouds_last_sync = self.zadjii_home.last_sync_time()

        req = MirrorHandshakeMessage(
            mirror_id=2,
            last_sync=None,
            last_modified=None,
            hostname='hostname',
            used_space=0,
            remaining_space=INFINITE_SIZE
        )

        resp = RemoteMirrorHandshakeMessage(id=2,
                                            new_sync=None,
                                            sync_end=datetime_to_string(clouds_last_sync),
                                            last_all_sync=None,
                                            hosts=[self.mirror_0.to_dict()])
        conn = self.expectResponse(req, resp)
        self.controller.filter_func(conn, '')


    def test_mirror_handshake_up_to_date(self):
        self.setup_default_clouds()

        clouds_last_sync = self.zadjii_home.last_sync_time()

        req = MirrorHandshakeMessage(
            mirror_id=2,
            last_sync=datetime_to_string(clouds_last_sync),
            last_modified=datetime_to_string(clouds_last_sync),
            hostname='hostname',
            used_space=0,
            remaining_space=INFINITE_SIZE
        )

        # everyone is up to date
        last_all_sync=datetime_to_string(clouds_last_sync)

        resp = RemoteMirrorHandshakeMessage(id=2,
                                            new_sync=datetime_to_string(clouds_last_sync),
                                            sync_end=None,
                                            last_all_sync=last_all_sync,
                                            hosts=None)
        conn = self.expectResponse(req, resp)
        self.controller.filter_func(conn, '')

    def test_mirror_handshake_up_to_date_none(self):
        self.setup_default_clouds()

        clouds_last_sync = self.zadjii_home.last_sync_time()

        req = MirrorHandshakeMessage(
            mirror_id=2,
            last_sync=datetime_to_string(clouds_last_sync),
            last_modified=None,
            hostname='hostname',
            used_space=0,
            remaining_space=INFINITE_SIZE
        )

        # everyone is up to date
        last_all_sync=datetime_to_string(clouds_last_sync)

        resp = RemoteMirrorHandshakeMessage(id=2,
                                            new_sync=datetime_to_string(clouds_last_sync),
                                            sync_end=None,
                                            last_all_sync=last_all_sync,
                                            hosts=None)
        conn = self.expectResponse(req, resp)
        self.controller.filter_func(conn, '')

    def test_mirror_handshake_new_update(self):
        self.setup_default_clouds()

        clouds_last_sync = self.zadjii_home.last_sync_time()
        later = clouds_last_sync + timedelta(1, 0, 0)

        req = MirrorHandshakeMessage(
            mirror_id=2,
            last_sync=datetime_to_string(clouds_last_sync),
            last_modified=datetime_to_string(later),
            hostname='hostname',
            used_space=0,
            remaining_space=INFINITE_SIZE
        )

        # mirror_1 has the new update, so mirror_0 is the oldest sync time
        last_all_sync=datetime_to_string(self.mirror_0.last_sync)

        resp = RemoteMirrorHandshakeMessage(id=2,
                                            new_sync=datetime_to_string(later),
                                            sync_end=None,
                                            last_all_sync=last_all_sync,
                                            hosts=None)
        conn = self.expectResponse(req, resp)
        self.controller.filter_func(conn, '')

        # ensure that the cloud's last_sync_time matches the value we just gave
        # it, since this mirror is now the latest to sync.
        self.assertEqual(later, self.zadjii_home.last_sync_time())


    def test_mirror_handshake_missed_update(self):
        self.setup_default_clouds()

        clouds_last_sync = self.zadjii_home.last_sync_time()
        earlier = clouds_last_sync - timedelta(1, 0, 0)

        req = MirrorHandshakeMessage(
            mirror_id=2,
            last_sync=datetime_to_string(clouds_last_sync),
            last_modified=datetime_to_string(earlier),
            hostname='hostname',
            used_space=0,
            remaining_space=INFINITE_SIZE
        )
        before_request = datetime.utcnow()
        # new_sync in the response will be whatever time the message came in. Verify manually:

        # resp = RemoteMirrorHandshakeMessage(id=1,
        #                                     new_sync=some_time,
        #                                     sync_end=None,
        #                                     last_all_sync=datetime_to_string(self.mirror_0.last_sync),
        #                                     hosts=None)
        conn = self.expectResponse(req, None)
        def on_send(msg):

            after_request = datetime.utcnow()
            self.assertEqual(REMOTE_MIRROR_HANDSHAKE, msg.type)
            self.assertEqual(2, msg.id)
            self.assertEqual(None, msg.hosts)
            self.assertEqual(None, msg.sync_end)
            self.assertNotEqual(None, msg.new_sync)
            self.assertNotEqual(None, msg.last_all_sync)
            new_sync = datetime_from_string(msg.new_sync)
            last_all_sync = datetime_from_string(msg.last_all_sync)

            # mirror_1 has the new update, so mirror_0 is the oldest sync time
            self.assertEqual(self.zadjii_home.last_all_sync(), last_all_sync)
            self.assertEqual(self.mirror_0.last_sync, last_all_sync)

            # We can't check the exact timestamp we assigned the cloud, but we
            # can ensure that it was between when we sent the request and when
            # we recieved it.
            self.assertTrue(earlier < new_sync, '{} < {}'.format(earlier, new_sync))
            self.assertTrue(clouds_last_sync < new_sync, '{} < {}'.format(clouds_last_sync, new_sync))
            self.assertTrue(before_request < new_sync, '{} < {}'.format(before_request, new_sync))
            self.assertTrue(new_sync < after_request, '{} < {}'.format(new_sync, after_request))

        conn.send_callback = on_send
        self.controller.filter_func(conn, '')

        # ensure that the cloud's last_sync_time has been updated to reflect
        # there's a mirror with a new last_sync value.
        self.assertTrue(clouds_last_sync < self.zadjii_home.last_sync_time())

def main():
    unittest.main()


if __name__ == '__main__':
    main()
