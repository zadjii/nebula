import os
from datetime import datetime
from host import _host_db as db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, backref
from FileNode import FileNode
from IncomingHostEntry import IncomingHostEntry

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
    children = relationship('FileNode', backref='cloud', lazy='dynamic')
    # root_node = relationship('FileNode', uselist=False, backref='cloud')
    remote_host = Column(String)
    remote_port = Column(Integer)
    incoming_hosts = relationship('IncomingHostEntry', backref='cloud', lazy='dynamic')
    completed_mirroring = Column(Boolean, default=False)

    # we might end up needing the message
    def create_or_update_node(self, full_path, file_transfer_msg, db):
        # msg = file_transfer_msg
        # file_isdir = msg['isdir']
        # file_size = msg['fsize']
        # rel_path = msg['fpath']
        curr_children = self.children
        curr_parent_node = None
        # curr_path = '.'
        dirs = os.path.normpath(full_path).split(os.sep)
        print 'create/update for all of {}'.format(dirs)
        while len(dirs) > 0:
            # find the node in children if it exists, else make it
            if curr_parent_node is not None:
                child = curr_children.filter_by(name=dirs[0]).first()
            else:
                child = self.children.filter_by(name=dirs[0]).first()
            if child is None:
                child = FileNode()
                child.name = dirs[0]
                child.created_on = datetime.utcnow()
                child.last_modified = child.created_on
                # child.cloud_id = self.id
                db.session.add(child)
                if curr_parent_node is not None:
                    curr_parent_node.children.append(child)
                else:
                    self.children.append(child)
                db.session.commit()
                print '\tcreated node for <{}>({}), parent:<{}>'\
                    .format(
                        child.name
                        , child.created_on
                        , curr_parent_node.name if curr_parent_node is not None else 'None'
                    )
            curr_parent_node = child
            curr_children = child.children
            dirs.pop(0)





