import os
import platform
from datetime import datetime

from common.SimpleDB import SimpleDB
from common_util import ResultAndData, get_mylog, get_free_space_bytes, INFINITE_SIZE, Error
from common.RelativePath import RelativePath
from connections.RawConnection import RawConnection
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from FileNode import FileNode, FILE_MOVED
from host.models import nebs_base as base
from messages import HostHandshakeMessage, FileSyncProposalMessage

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
    max_size = Column(Integer)  # Cloud size in bytes
    root_directory = Column(String)

    # If you find yourself setting the cloud value of a FileNode, you're
    #   probably doing something wrong.
    # The only nodes that should have cloud set are ones that are children of
    #   the root node. Otherwise, the root will think ALL nodes are
    #   it's children. The Cloud(mirror) model only has one children
    #   relationship, whose backref is cloud, so if you set a filenode's cloud,
    #   then the cloud will think that filenode is a child of the root.
    children = relationship('FileNode', backref='cloud', lazy='dynamic')
    incoming_hosts = relationship('IncomingHostEntry', backref='cloud', lazy='dynamic')
    completed_mirroring = Column(Boolean, default=False)

    # todo this needs to be a many-many, sessions have lots of clouds, clouds
    # cont have lots of sessions.
    clients = relationship('Client', backref='cloud', lazy='dynamic')

    def __init__(self, uname, cname, root_dir):
        # type: (str, str, str) -> None
        self.mirrored_on = datetime.utcnow()
        self.username = uname
        self.name = cname
        self.root_directory = root_dir

    def full_name(self):
        return '{}/{}'.format(self.uname(), self.cname())

    def cname(self):
        return self.name

    def uname(self):
        return self.username

    def get_remote_conn(self):
        # type: () -> ResultAndData
        # type: () -> ResultAndData(True, RawConnection)
        # type: () -> ResultAndData(False, Exception)
        from host.util import setup_remote_socket

        rd = ResultAndData(False, None)
        try:
            rd = setup_remote_socket(self)
            if rd.success:
                conn = RawConnection(rd.data)
                rd = ResultAndData(True, conn)
            else:
                return rd
        except Exception as e:
            rd = ResultAndData(False, e)
        return rd

    def make_tree(self, relative_path, db, created_on=None):
        # type: (RelativePath, SimpleDB, datetime) -> FileNode
        node, new_nodes = self._make_tree_get_all(relative_path, db, created_on=created_on)
        return node

    def _make_tree_get_all(self, relative_path, db, created_on=None):
        # type: (RelativePath, SimpleDB, datetime) -> (FileNode, [FileNode])
        """
        Either retreives the existing FileNode corresponding to the given path,
        or creates the tree for the given path.
        return: the FileNode for the given relative_path
                and any new nodes we created
        """
        curr_children = self.children
        curr_parent_node = None
        dirs = relative_path.to_elements_no_root()
        new_nodes = []
        while len(dirs) > 0:
            # find the node in children if it exists, else make it
            child = curr_children.filter_by(name=dirs[0]).first()
            if child is None:
                child = FileNode(dirs[0], created_on=created_on)
                db.session.add(child)
                if curr_parent_node is not None:
                    curr_parent_node.children.append(child)
                else:
                    self.children.append(child)
                new_nodes.append(child)
            curr_parent_node = child
            curr_children = child.children
            dirs.pop(0)
        # at this point, the curr_parent_node is the node that is the file we created
        return curr_parent_node, new_nodes

    def get_child_node(self, relative_path):
        """
        Returns the node in this mirror corresponding to `relative_path`.
        If the path does not exist under this mirror, returns None.
        If the path corresponds to the root of the mirror, it returns this
        object (a host.models.Cloud). Callers should not assume that the
        returned object is a FileNode, and use result.is_root() to deterine if
        the returned object is a FileNode or a Cloud.
        """
        # type: (RelativePath) -> Any(None, Cloud, FileNode)
        if relative_path.is_root():
            return self

        target_path_elems = relative_path.to_elements_no_root()

        curr_child = None
        while len(target_path_elems) > 0:
            curr_file = target_path_elems[0]
            curr_child = curr_child.children.filter_by(name=curr_file).first()
            target_path_elems.pop(0)
            if curr_child is not None:
                # This is a match to the current path elem. Continue on it's children.
                pass
            else:
                # We did not fnd a match to the current path element. The
                #   relative path does not exist in this cloud.
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

    # def generate_handshake(self, ip, port, ws_port):
    #     used_space = self.get_used_size()
    #     if self.max_size == INFINITE_SIZE:
    #         remaining_space = get_free_space_bytes('/')
    #     else:
    #         remaining_space = self.max_size - used_space
    #     host_id = self.remote.my_id_from_remote
    #     mirror_id = self.my_id_from_remote
    #     hostname = platform.uname()[1]
    #     # TODO: HostHandshakeMessage should only be used for the Host->Remote
    #     # SSL handshake, and updating address and such. We should be using
    #     # MirrorHandshakeMessage for updating the timestamp of a particular
    #     # mirror.
    #     msg = HostHandshakeMessage(
    #         id=mirror_id,
    #         ipv6=ip,
    #         port=port,
    #         wsport=ws_port,
    #         last_sync=self.last_sync().isoformat() + 'Z',
    #         last_modified=self.last_modified().isoformat() + 'Z',
    #         hostname=hostname,  # hostname
    #         used_space=used_space,
    #         remaining_space=remaining_space
    #     )
    #     return msg


    def generate_mirror_handshake(self):
        # type: () -> HostHandshakeMessage
        used_space = self.get_used_size()
        if self.max_size == INFINITE_SIZE:
            remaining_space = get_free_space_bytes('/')
        else:
            remaining_space = self.max_size - used_space

        mirror_id = self.my_id_from_remote
        hostname = platform.uname()[1]

        # last_modified() will automatically determine our latest modification,
        # based on the timestamps of our children.

        msg = MirrorHandshakeMessage(
            mirror_id=mirror_id,
            last_sync=self.last_sync().isoformat() + 'Z',
            last_modified=self.last_modified().isoformat() + 'Z',
            hostname=hostname,  # hostname
            used_space=used_space,
            remaining_space=remaining_space
        )
        return msg

    def get_my_id_from_remote(self):
        return self.my_id_from_remote

    def all_children(self):
        # type: () -> [FileNode]
        return self.children.all()

    def last_sync(self):
        # type: () -> datetime
        """
        Determines the last_sync timestamp of this cloud, by looking for the
        newest last_sync of our children.
        This can return None if we have no children, or if we only have children
            that haven't yet been synced.
        :return:
        """
        newest = None
        for child in self.all_children():
            child_last_recursive = child.last_sync_recursive()
            if newest is None or child_last_recursive > newest:
                newest = child_last_recursive
        return newest

    def last_modified(self):
        # type: () -> datetime
        """
        Returns the last_modified timestamp of this cloud, by looking for the
        newest modified child of all it's children
        """
        newest = None
        for child in self.children.all():
            child_recursive = child.last_modified_recursive()
            if newest is None or child_recursive > newest:
                newest = child_recursive
        return newest

    def modified_since_last_sync(self):
        # type () -> [FileNode]
        """
        Returns all child nodes that have been modified since they were last sync'd.
        If everyone's most recent state has been sync'd, then this returns an empty list.
        If a node was added, then it should be in this list (it's last_sync will be None)
        These are the pending changes
        :return:
        """
        nodes = []
        for child in self.children.all():
            child_unsynced = child.unsynced_children_inclusive()
            nodes.extend(child_unsynced)
        return nodes


    def modified_between(self, sync_start, sync_end):
        # type (datetime, datetime) -> [FileNode]
        """
        Returns all child nodes that have been modified in the timeframe [sync_start, sync_end]
        TODO: Should that be an inclusive or exclusive range?
        :return:
        """
        nodes = []
        for child in self.children.all():
            # TODO:
            # child_unsynced = child.modfied_children_inclusive(sync_start, sync_end)
            nodes.extend(child_unsynced)
        return nodes

    def get_change_proposals(self, db):
        # type: (SimpleDB) -> [FileSyncProposalMessage]
        """
        Generates a list of FileChangeProposals describing the set of changes we
        have that haven't synced.
        The caller should make sure to fill in the mirror_id param of these
        messages with the id of the intended recipient.
        :param db:
        :return:
        """
        _log = get_mylog()
        proposals = []
        modified_nodes = self.modified_since_last_sync()
        for node in modified_nodes:
            change_type = node.get_update_type()
            rel_src_path = node.relative_path()
            rel_tgt_path = None
            if change_type == FILE_MOVED:
                tgt_node_id = node.moved_to_id
                tgt_node = db.session.query(FileNode).get(tgt_node_id)
                if tgt_node is None:
                    _log.error('{} said it was moved, but the id it was moved to ({}) doesnt exist'.format(rel_src_path.to_string(), tgt_node_id))
                    continue
                rel_tgt_path = tgt_node.relative_path()

            # TODO: I do NOT like this. I'd really rather that the db models
            #   remain independent from the actual filesystem. There should
            #   probably be an IFileSysteminfo interface that the HostController
            #   can pass to these methods.
            # Then, the unittests can override as necessary (to fake a filesystem)
            is_dir = os.path.isdir(rel_src_path.to_absolute(self.root_directory))

            # TODO: the mirror_id param - is that the source mirror or the target mirror?
            # would the mirror proposing know the ID of the mirror it should be intended for?
            # A FileSyncRequest sure could include the ID of the requestor and
            #   the id of the mirror it's requesting from (our id)
            #   So that path could fill in the mirror_id with the id of the
            #   intended recipient.
            # When we get a RemoteHandshake suggesting that we need to send
            #       updates to other hosts, we could generate this list of
            #       proposals, then fill in the mirror_id for the intended
            #       recipient as we iterate over them.
            proposal = FileSyncProposalMessage(
                mirror_id=self.my_id_from_remote,
                rel_path=rel_src_path,
                tgt_path=rel_tgt_path,
                change_type=change_type,
                is_dir=is_dir,
                sync_time=node.last_sync
            )
            proposals.append(proposal)
        return proposals

    def create_file(self, full_path, db, timestamp=None):
        # type: (str) -> ResultAndData

        rel_path = RelativePath()
        rd = rel_path.from_absolute(self.root_directory, full_path)
        if not rd.success:
            return rd

        child_node = self.get_child_node(rel_path)
        if child_node is not None:
            return Error('Cannot create a file that already exists')

        node = self.make_tree(relative_path=rel_path, db=db, created_on=timestamp)
        # Caller will commit the DB changes
        rd = ResultAndData(node is not None, node)
        return rd

    def modify_file(self, full_path, db, timestamp=None):
        # type: (str) -> ResultAndData
        rel_path = RelativePath()
        rd = rel_path.from_absolute(self.root_directory, full_path)
        if not rd.success:
            return rd

        child_node = self.get_child_node(rel_path)
        if child_node is None:
            return Error('Cannot modify a file that does not exist')
        if child_node.is_root():
            # TODO: you can't modify the root, right? that doesn't make sense
            return Error('Cant modify the root')
        child_node.modify(timestamp)
        # Caller will commit the DB changes
        return ResultAndData(True, child_node)

    def delete_file(self, full_path, db, timestamp=None):
        # type: (str) -> ResultAndData
        rel_path = RelativePath()
        rd = rel_path.from_absolute(self.root_directory, full_path)
        if not rd.success:
            return rd

        child_node = self.get_child_node(rel_path)
        if child_node is None:
            return Error('Cannot delete a file that does not exist')
        if child_node.is_root():
            # TODO: you can't modify the root, right? that doesn't make sense
            return Error('Cant modify the root')
        child_node.delete(timestamp=timestamp)
        # Caller will commit the DB changes
        return ResultAndData(True, child_node)

    def move_file(self, full_src_path, full_target_path, db):
        # type: (str, str) -> ResultAndData

        rel_src_path = RelativePath()
        rd = rel_src_path.from_absolute(self.root_directory, full_src_path)
        if not rd.success:
            return rd

        rel_tgt_path = RelativePath()
        rd = rel_tgt_path.from_absolute(self.root_directory, full_target_path)
        if not rd.success:
            return rd

        child_src_node = self.get_child_node(rel_src_path)
        if child_node is None:
            return Error('Cannot move a file that does not exist')
        if child_src_node.is_root():
            # TODO: you can't modify the root, right? that doesn't make sense
            return Error('Cant modify the root')

        # TODO: do we allow moving files to paths that already exist?
        # child_tgt_node = self.get_child_node(rel_tgt_path)
        # if child_tgt_node is not None:
        #     return Error('Cannot move a file to a path that already exists')
        child_tgt_node = self.make_tree(rel_tgt_path, db)
        if child_tgt_node.is_root():
            # TODO: you can't modify the root, right? that doesn't make sense
            return Error('Cant modify the root')
        child_src_node.move(child_tgt_node)
        # Caller will commit the DB changes
        return ResultAndData(child_tgt_node is not None, child_tgt_node)


