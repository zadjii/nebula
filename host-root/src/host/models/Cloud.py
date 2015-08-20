from host import host_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from FileNode import FileNode

__author__ = 'Mike'


class Cloud(db.Base):
    __tablename__ = 'cloud'

    id = Column(Integer, primary_key=True)
    my_id_from_remote = Column(Integer)
    name = Column(String)
    created_on = Column(DateTime)
    mirrored_on = Column(DateTime)

    last_update = Column(DateTime)
    max_size = Column(Integer)  # Cloud size in bytes

    root_directory = Column(String)
    files = relationship('FileNode', backref='cloud', lazy='dynamic')
    # root_node = relationship('FileNode', uselist=False, backref='cloud')
    remote_host = Column(String)
    remote_port = Column(Integer)

