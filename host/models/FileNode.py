from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from host.models import nebs_base as base
import os
from common.RelativePath import RelativePath

__author__ = 'Mike'

FILE_CREATED = 0
FILE_MODIFIED = 1
FILE_MOVED = 2
FILE_DELETED = 3

class FileNode(base):
    __tablename__ = 'filenode'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('filenode.id'))
    cloud_id = Column(Integer, ForeignKey('cloud.id'))
    name = Column(String)
    created_on = Column(DateTime)
    last_modified = Column(DateTime)
    last_sync = Column(DateTime)
    deleted_on = Column(DateTime, default=None)
    moved_to_id = Column(Integer, ForeignKey('filenode.id'))
    children = relationship('FileNode'
                            , foreign_keys=[parent_id]
                            , backref=backref('parent', remote_side=[id])
                            , lazy='dynamic')

    def __init__(self, name, created_on=None):
        self.name = name
        self.created_on = created_on or datetime.utcnow()
        self.last_modified = self.created_on

    def is_root(self):
        return False

    def relative_path(self):
        # type: () -> RelativePath
        """
        Returns this file's path, relative to the cloud root. "/" is the root
            of the mirror.
        :return:
        """
        path_str = self.name
        if self.parent is not None:
            path_str = os.path.join(self.parent.relative_path().to_string(), self.name)
        # else:
        #     return os.path.join('/', self.name)
        rp = RelativePath()
        rd = rp.from_relative(path_str)
        return None if not rd.success else rp

    def get_mirror(self):
        # type: () -> Cloud
        if self.cloud is not None:
            return self.cloud
        else:
            return self.parent.get_mirror()

    def has_been_deleted(self):
        # type: () -> bool
        return self.deleted_on is not None

    def modify(self, timestamp=None):
        if timestamp is None:
            timestamp = datetime.utcnow()
        self.last_modified = timestamp

    def delete(self, timestamp=None):
        # type: (datetime) -> None
        if timestamp is None:
            timestamp = datetime.utcnow()
        self.modify(timestamp)
        self.deleted_on = timestamp

    def can_be_pruned(self, last_all_sync):
        # type: (datetime) -> bool
        """
        Returns true if the node is deleted, our last_sync>=last_modified, and
        our last_sync is older than last_all_sync.
        """
        # TODO
        return False

    def move(self, target_node, timestamp=None):
        # type: (FileNode, datetime) -> None
        if timestamp is None:
            timestamp = datetime.utcnow()
        self.delete(timestamp)
        self.moved_to_id = target_node.id

    def unsynced(self):
        # type: () -> bool
        """
        Returns true if the current node's state hasn't been synced.
        """
        return (self.last_sync is None) or (self.last_modified > self.last_sync)

    def unsynced_children(self):
        # type: () -> [FileNode]
        """
        Returns all of the children of this node that are unsynced. Does NOT include this node.
        """
        nodes = []
        for child in self.children.all():
            child_unsynced = child.unsynced_children_inclusive()
            nodes.extend(child_unsynced)
        return nodes

    def unsynced_children_inclusive(self):
        # type: () -> [FileNode]
        """
        Returns all of the children of this node that are unsynced
        """
        nodes = self.unsynced_children()
        if self.unsynced():
            nodes.append(self)
        return nodes

    def sync(self, timestamp):
        # type: () -> None
        self.last_sync = timestamp

    def last_sync_recursive(self):
        # type: () -> datetime
        """
        Returns the newest sync timestamp of us or all our children.
        Called at the root of the tree, it will tell you the last time the cloud
        was sync'd with the remote.
        See host.models.Cloud::last_sync
        :return:
        """
        newest = self.last_sync
        for child in self.children.all():
            child_recursive = child.last_sync_recursive()
            if newest is None or (child_recursive is not None and child_recursive > newest):
                newest = child_recursive
        return newest

    def last_modified_recursive(self):
        # type: () -> datetime
        """
        Returns the greatest last_modified timestamp of this node and all it's
        children, recursively.
        """
        newest = self.last_modified
        for child in self.children.all():
            child_recursive = child.last_modified_recursive()
            if child_recursive > newest:
                newest = child_recursive
        return newest
