from datetime import datetime, timedelta
from uuid import uuid4

from common_util import Error, get_mylog
from common_util import ResultAndData
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, BigInteger
from sqlalchemy.orm import relationship, backref
from remote.models.ClientCloudHostMapping import ClientCloudHostMapping
from remote.models import nebr_base as base
__author__ = 'Mike'


class Session(base):
    __tablename__ = 'session'

    id = Column(Integer, primary_key=True)
    # cloud_id = Column(ForeignKey('cloud.id'))
    user_id = Column(ForeignKey('user.id'))
    host_id = Column(ForeignKey('host.id'))
    uuid = Column(String)  # todo:11 length should be the uuid length
    # todo:11 fix the type of this ^
    created_on = Column(DateTime)
    last_refresh = Column(DateTime)

    host_mappings = relationship('ClientCloudHostMapping'
                                 , backref='session'
                                 , lazy='dynamic')


    def __init__(self, user):
        now = datetime.utcnow()
        self.created_on = now
        self.last_refresh = now
        self.user = user
        sess_uuid = str(uuid4())
        self.uuid = sess_uuid
        # todo:11 this is probably bad. Maybe store the numeric value or something.

    def has_timed_out(self):
        # _log = get_mylog()
        delta = datetime.utcnow() - self.last_refresh
        return (delta.total_seconds()/60) > 30
        # _log.debug('Session {} is {}s old'.format(self.uuid, delta.total_seconds()))
        # return (delta.total_seconds()) > 3

    def refresh(self):
        now = datetime.utcnow()
        # only update the last refresh if the last refrest was in the past.
        # We're implementing stay_logged_in by setting the last_refresh to 1yr in the future
        if self.last_refresh < now:
            self.last_refresh = datetime.utcnow()
        # print('timeout time {}'.format(self.last_refresh))

    def get_user(self):
        print 'Session get_user, {}'.format(self.uuid)
        # type: () -> ResultAndData
        if self.user is None:
            rd = Error('No user exists on remote\'s session, sid:{}'.format(self.uuid))
        else:
            rd = ResultAndData(True, self.user)
        return rd
