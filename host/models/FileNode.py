from host import _host_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref


__author__ = 'Mike'


class FileNode(db.Base):
    __tablename__ = 'filenode'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('filenode.id'))
    cloud_id = Column(Integer, ForeignKey('cloud.id'))
    name = Column(String)
    created_on = Column(DateTime)
    last_modified = Column(DateTime)
    children = relationship('FileNode'
                            , backref=backref('parent', remote_side=[id])
                            , lazy='dynamic')


