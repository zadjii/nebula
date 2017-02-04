from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from host.models import nebs_base as base
__author__ = 'Mike'


class IncomingHostEntry(base):
    __tablename__ = 'incoming_host_entry'

    id = Column(Integer, primary_key=True)
    their_id_from_remote = Column(Integer)
    cloud_id = Column(Integer, ForeignKey('cloud.id'))
    created_on = Column(DateTime)
    their_address = Column(String)

