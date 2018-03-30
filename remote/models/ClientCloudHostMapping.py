from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, BigInteger
from sqlalchemy.orm import relationship, backref
from remote.models import nebr_base as base

__author__ = 'Mike'


class ClientCloudHostMapping(base):
    __tablename__ = 'clientcloudhostmapping'
    id = Column(Integer, primary_key=True)
    session_id = Column(ForeignKey('session.id'))
    cloud_id = Column(ForeignKey('cloud.id'))
    host_id = Column(ForeignKey('mirror.id'))

    def __init__(self, session, cloud, host):
        # Remember, if this isn't added to the DB, then the backrefs won't be
        #   hooked up from the other side.
        # So instantiating this without a session (for the public user) is
        #   fraught with peril
        self.session_id = session.id if session else None
        self.cloud_id = cloud.id
        self.host_id = host.id


