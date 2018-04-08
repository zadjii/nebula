import base64
import uuid
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, BigInteger
from sqlalchemy.orm import relationship, backref
from remote.models import nebr_base as base

__author__ = 'Mike'


class CloudLink(base):
    __tablename__ = 'cloudlink'
    id = Column(Integer, primary_key=True)
    cloud_id = Column(ForeignKey('cloud.id'))
    link_string = Column(String)

    def __init__(self, cloud, db):
        # type: (Cloud, SimpleDB) -> None
        self.cloud_id = cloud.id
        found = False
        proposed_string = ''
        while not found:
            proposed_string = base64.urlsafe_b64encode(str(uuid.uuid4()))[0:8]
            other = db.session.query(CloudLink).filter_by(link_string=proposed_string).first()
            found = other is not None
        self.link_string = proposed_string


