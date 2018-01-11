import os
import platform
from datetime import datetime

from common_util import ResultAndData, mylog, get_free_space_bytes, INFINITE_SIZE
from connections.RawConnection import RawConnection
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, backref
from FileNode import FileNode
from host.models import nebs_base as base
from messages import HostHandshakeMessage

__author__ = 'Mike'


class Cloud(base):
    __tablename__ = 'cloud'
    """
    This should more accurately be called a Mirror, this represents one
        mirror of a cloud on a host.
    """
    id = Column(Integer, primary_key=True)
    remote_id = Column(ForeignKey('remote.id'))

    name = Column(String)  # cloudname
    username = Column(String)  # uname
    my_id_from_remote = Column(Integer)
    created_on = Column(DateTime)
    mirrored_on = Column(DateTime)

    last_update = Column(DateTime)
    max_size = Column(Integer)  # Cloud size in bytes

    root_directory = Column(String)
    children = relationship('FileNode', backref='cloud', lazy='dynamic')
    incoming_hosts = relationship('IncomingHostEntry', backref='cloud', lazy='dynamic')
    completed_mirroring = Column(Boolean, default=False)

    # todo this needs to be a many-many, sessions have lots of clouds, clouds
    # cont have lots of sessions.
    clients = relationship('Client', backref='cloud', lazy='dynamic')

    def full_name(self):
        return '{}/{}'.format(self.uname(), self.cname())

    def cname(self):
        return self.name

    def uname(self):
        return self.username

    def get_remote_conn(self):
        from host.util import setup_remote_socket

        rd = ResultAndData(False, None)
        try:
            rd = setup_remote_socket(self)
            if rd.success:
                conn = RawConnection(rd.data)
                rd = ResultAndData(True, conn)
            else:
                return rd
        except Exception, e:
            rd = ResultAndData(False, e)
        return rd

    def translate_relative_path(self, rel_path):
        # todo make sure all paths are actually relative paths.
        if rel_path == '/':
            return self.root_directory
        full_path = os.path.join(self.root_directory, rel_path)
        return full_path

    # we might end up needing the message
    def create_or_update_node(self, full_path, db):
        curr_children = self.children
        curr_parent_node = None
        # curr_path = '.'
        dirs = os.path.normpath(full_path).split(os.sep)
        # mylog('create or update dirs={}'.format(dirs))
        # print 'create/update for all of {}'.format(dirs)
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
                # child.cloud = self
                db.session.add(child)
                if curr_parent_node is not None:
                    curr_parent_node.children.append(child)
                    # mylog('[{}] {} attached to node {}'.format(self.my_id_from_remote, child.name, curr_parent_node.name))
                else:
                    self.children.append(child)
                    # mylog('[{}] {} attached to mirror'.format(self.my_id_from_remote, child.name,))
                db.session.commit()
                # mylog('\tcreated node for <{}>, parent:<{}>'\
                #     .format(
                #         child.name
                #         , curr_parent_node.name if curr_parent_node is not None else 'None'
                #     )
                # )
            curr_parent_node = child
            curr_children = child.children
            dirs.pop(0)
        # at this point, the curr_parent_node is the node that is the file we created
        return curr_parent_node

    def get_child_node(self, relative_path):
        # type: (str) -> Any(Cloud, FileNode)
        target_path_elems = os.path.normpath(relative_path).split(os.sep)
        if target_path_elems[0] == '.':
            target_path_elems.pop(0)

        curr_child = self
        while len(target_path_elems) > 0:
            curr_file = target_path_elems[0]
            child = curr_child.children.filter_by(name=curr_file).first()
            curr_child = child
            target_path_elems.pop(0)
            if child is not None:
                # This is a match to the current path elem. Continue on it's children.
                pass
            else:
                break

        # curr_child is either self, or a FileNode
        return curr_child

    def is_root(self):
        return True

    def get_used_size(self):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.root_directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def generate_handshake(self, ip, port, ws_port):
        used_space = self.get_used_size()
        if self.max_size == INFINITE_SIZE:
            remaining_space = get_free_space_bytes('/')
        else:
            remaining_space = self.max_size - used_space

        host_id = self.remote.my_id_from_remote
        mirror_id = self.my_id_from_remote
        hostname = platform.uname()[1]
        msg = HostHandshakeMessage(
            mirror_id,
            ip,
            port,
            ws_port,
            0,  # todo update number/timestamp? it's in my notes
            hostname,  # hostname
            used_space,
            remaining_space
        )
        return msg






