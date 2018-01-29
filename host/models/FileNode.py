from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from host.models import nebs_base as base
import os
__author__ = 'Mike'


class FileNode(base):
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

    def is_root(self):
        return False

    def full_path(self):
        """
        Returns this file's path, relative to the cloud root. "/" is the root
            of the mirror.
        :return:
        """
        if self.parent is not None:
            return os.path.join(self.parent.full_path(), self.name)
        else:
            return os.path.join('/', self.name)

    def get_mirror(self):
        # type: () -> Cloud
        if self.cloud is not None:
            return self.cloud
        else:
            return self.parent.get_mirror()

