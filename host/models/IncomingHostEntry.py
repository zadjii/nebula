from host import _host_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from FileNode import FileNode
from models import nebs_base as base
__author__ = 'Mike'


class IncomingHostEntry(base):
    __tablename__ = 'incoming_host_entry'

    id = Column(Integer, primary_key=True)
    their_id_from_remote = Column(Integer)
    cloud_id = Column(Integer, ForeignKey('cloud.id'))
    created_on = Column(DateTime)
    their_address = Column(String)

