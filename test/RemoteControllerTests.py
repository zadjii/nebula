import unittest
from datetime import timedelta
from common_util import *
from connections.AbstractConnection import AbstractConnection
from messages import *
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

        self.zadjii_home = Cloud(self.zadjii)
        self.zadjii_home.name = 'home'
        self.db.session.add(self.zadjii_home)
        self.zadjii_work = Cloud(self.zadjii)
        self.zadjii_work.name = 'work'
        self.db.session.add(self.zadjii_work)

        self.host_0 = Host()
        self.host_1 = Host()
        self.db.session.add(self.host_0)
        self.db.session.add(self.host_1)
        self.db.session.commit()

        self.mirror_0 = Mirror(self.zadjii_home, self.host_0)
        self.db.session.add(self.mirror_0)

        # Initialize the host, cloud with some sane defaults.
        # * mirror_0 is the most recently sync'd mirror, and it's active
        # * host_0 (on which mirror_0 is hosted) is also active
        now = datetime.utcnow()
        self.mirror_0.last_sync = now
        self.mirror_0.last_handshake = now
        self.mirror_0.completed_mirroring = True
        self.host_0.last_update = now

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

        # clouds_last_sync = self.mirror_0.last_sync
        # later = clouds_last_sync + timedelta(1, 0, 0)

        clouds_last_update = self.zadjii_home.last_update
        later = clouds_last_update + timedelta(1, 0, 0)

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

        clouds_last_update = self.zadjii_home.last_update
        earlier = clouds_last_update - timedelta(1, 0, 0)

        req = MirrorHandshakeMessage(
            mirror_id=1,
            last_sync=datetime_to_string(earlier),
            last_modified=datetime_to_string(earlier),
            hostname='hostname',
            used_space=0,
            remaining_space=INFINITE_SIZE
        )

        resp = RemoteMirrorHandshakeMessage(id=1,
                                            new_sync=None,
                                            sync_end=datetime_to_string(clouds_last_update),
                                            last_all_sync=None,
                                            hosts=[self.mirror_0.to_dict()])
        conn = self.expectResponse(req, resp)
        self.controller.filter_func(conn, '')

def main():
    unittest.main()


if __name__ == '__main__':
    main()
