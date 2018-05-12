"""
PrivateData is the model that backs .nebs data.

This provides an abstraction layer on top of otherwise plain .json data
"""
import base64
import posixpath
import uuid

from common_util import mylog, ResultAndData, get_path_elements, PUBLIC_USER_ID, RelativePath
import os
import json

# Fuck all this versioning shit, it's trash and I hate that I even started it
CURRENT_MAJOR_VERSION = 0
CURRENT_MINOR_VERSION = 0

MAJ_VER_KEY = 'major_version'
MIN_VER_KEY = 'minor_version'
LINKS_KEY = 'links'
GROUPS_KEY = 'groups'
FILES_KEY = 'files'

NO_ACCESS = 0
READ_ACCESS = 1
WRITE_ACCESS = 2
RDWR_ACCESS = READ_ACCESS | WRITE_ACCESS
SHARE_ACCESS = 4
FULL_ACCESS = SHARE_ACCESS | WRITE_ACCESS | READ_ACCESS

PUBLIC_ID = 0
OWNERS_ID = 1
FIRST_GROUP_ID = 2

class Group(object):
    def __init__(self, id, name, user_ids):
        self.id = id
        self._user_ids = user_ids
        self.name = name

    def has_user(self, user_id):
        # type: (int) -> bool
        return user_id in self._user_ids if not self.is_public() else True

    def add_user(self, user_id):
        # NOTE: If we try and add a user to the "public" group, then it will
        #   stop being the public group
        # however, we'll think they're already in the group, so this should work
        if not self.has_user(user_id):
            self._user_ids.append(user_id)

    def is_public(self):
        return self._user_ids == []

    def to_serializable(self):
        return {
            'id': self.id
            , 'name': self.name
            , 'user_ids': self._user_ids
        }

    def from_serializable(self, obj):
        self.id = obj['id']
        self._user_ids = obj['user_ids']
        self.name = obj['name']


def make_public_group():
    return Group(PUBLIC_ID, 'public', [])


def make_owners_group(owner_ids):
    # type: ([int]) -> Group
    return Group(OWNERS_ID, 'owners', owner_ids)


class Link(object):
    def __init__(self, path, user_ids, access, id):
        # type: (str, [int], int, str) -> None
        self._path = path
        self._user_ids = user_ids
        self._access = access
        self.id = id

    def has_permissions(self):
        """
        If there aren't any users in the link, then we should use the file's
        permissions instead
        :return:
        """
        return self._user_ids is not []

    def has_user(self, user_id):
        # type: (int) -> bool
        # return self.is_public() or (user_id in self._user_ids)
        return user_id in self._user_ids

    def get_access(self):
        return self._access

    def get_path(self):
        return self._path

    def add_user(self, user_id):
        # type: (int) -> None
        if not self.has_user(user_id):
            self._user_ids.append(user_id)

    def to_serializable(self):
        return {
            'path': self._path
            , 'user_ids': self._user_ids
            , 'access': self._access
            , 'id': self.id
        }

    def from_serializable(self, obj):
        self._path = obj['path']
        self._user_ids = obj['user_ids']
        self._access = obj['access']
        self.id = obj['id']


class FilePermissions(object):
    def __init__(self, path):
        self._groups = {}  # gid->permission mappings
        self._users = {}  # uid->permission mappings
        self._filepath = path  # the cloud relative path

    def add_user(self, user_id, permissions):
        # type: (int, int) -> ResultAndData
        rd = ResultAndData(False, None)
        if user_id in self.get_user_ids():
            old_perm = self._users[str(user_id)]
            self._users[str(user_id)] = permissions
            rd = ResultAndData(True, old_perm)
        else:
            self._users[str(user_id)] = permissions
            rd = ResultAndData(True, None)
        return rd

    def add_group(self, group_id, permissions):
        # type: (int, int) -> ResultAndData
        rd = ResultAndData(False, None)
        if group_id in self.get_group_ids():
            old_perm = self._groups[str(group_id)]
            self._groups[str(group_id)] = permissions
            rd = ResultAndData(True, old_perm)
        else:
            self._groups[str(group_id)] = permissions
            rd = ResultAndData(True, None)
        return rd

    def get_group_ids(self):
        # type: () -> [int]
        return [int(gid) for gid in self._groups.keys()]

    def get_user_ids(self):
        # type: () -> [int]
        return [int(uid) for uid in self._users.keys()]

    def get_user_permissions(self, user_id):
        # type: (int) -> int
        if user_id in self.get_user_ids():
            return self._users[str(user_id)]
        return NO_ACCESS

    def get_group_permissions(self, group_id):
        # type: (int) -> int
        if group_id in self.get_group_ids():
            return self._groups[str(group_id)]
        return NO_ACCESS

    def to_serializable(self):
        return {
            'path': self._filepath
            , 'groups': self._groups
            , 'users': self._users
        }

    def from_serializable(self, obj):
        self._filepath = obj['path']
        self._groups = obj['groups']
        self._users = obj['users']


class PrivateData(object):
    def __init__(self, cloud, owner_ids):
        # self._cloud = cloud
        self._cloud_id = cloud.id
        self._cloud_root = cloud.root_directory
        self._version = (CURRENT_MAJOR_VERSION, CURRENT_MINOR_VERSION)
        self._links = []
        self._groups = [make_public_group(), make_owners_group(owner_ids)]
        self._files = {}  # { str -> FilePermissions }
        self._next_group_id = FIRST_GROUP_ID
        # try reading the .nebs from the cloud.
        # if it doesn't exist, then write out the defaults.
        if self._file_exists():
            mylog('Reading .nebs for cloud: '
                  '[{}]"{}"'.format(cloud.my_id_from_remote, cloud.name))
            rd = self.read_backend()
            if rd.success:
                mylog('read backend data')
                self.read_json(rd.data)
            else:
                mylog('Error reading backend data: {}'.format(rd.data))
                raise Exception  # todo:fixme
        else:
            if owner_ids is None:
                mylog('We\'re creating the .nebs for the cloud, but we '
                      'specified no owners. \n'
                      'This will prevent anyone from accessing this cloud. \n'
                      'This is likely a programming error. \n'
                      'Make sure when the cloud is mirrored, we gave it \n'
                      'owner_ids, and that if this file accidentally gets \n'
                      'deleted, we recover it intelligently.', '31')
                # assert?
            mylog('Creating .nebs for cloud: '
                  '[{}]"{}"'.format(cloud.my_id_from_remote, cloud.name))
            root_path = os.path.join(cloud.root_directory, './')

            root_path = os.path.normpath(root_path)
            root_path = os.path.relpath(root_path, cloud.root_directory)
            root_perms = FilePermissions(root_path)
            root_perms.add_group(OWNERS_ID, FULL_ACCESS)
            self._files[root_path] = root_perms
            self.commit()

    def get_group(self, group_id):
        for g in self._groups:
            if g.id == group_id:
                return g
        return None

    def get_permissions(self, user_id, relative_path):
        # type: (int, RelativePath) -> int
        """
        HEY DUMBASS. Make sure you normalize the path before here.
        Get rid of trailing slashes on dirs. Make sure it's actually in the
        cloud's tree. stuff like that.
        Don't pass in the full local path. Pass in the corrected, relative path.
        :param user_id:
        :param relative_path:
        :return:
        """
        filepath = relative_path.to_string()
        # break the path into elements, start from the root, work down
        path_elems = get_path_elements(filepath)
        curr_path = '.'  # always start by checking the root
        current_perms = NO_ACCESS
        i = 0
        # I'm so sorry that this loop is structured weird
        while i <= len(path_elems) and current_perms < RDWR_ACCESS:
            rp = RelativePath()
            rp.from_relative(curr_path)
            curr_corrected = rp.to_string()
            mylog('checking {}\'s perms for {}'.format(user_id, curr_corrected))
            if curr_corrected in self._files:
                file_perms = self._files[curr_corrected]
                new_perms = self._file_get_permissions(user_id, file_perms)
                mylog('found new permission {} for {}'.format(new_perms, curr_corrected))
                current_perms |= new_perms
            if i < len(path_elems):
                curr_path = os.path.join(curr_corrected, path_elems[i])
            i += 1
        return current_perms


    def get_permissions_no_recursion(self, user_id, relative_path):
        # type: (int, RelativePath) -> int
        curr_corrected = relative_path.to_string()
        if curr_corrected in self._files:
            file_perms = self._files[curr_corrected]
            new_perms = self._file_get_permissions(user_id, file_perms)
            return new_perms
        return NO_ACCESS

    def get_link_permissions(self, user_id, link_str):
        matching_link = None
        for link in self._links:
            if link.id == link_str:
                matching_link = link
                break
        if matching_link is None:
            return NO_ACCESS
        if matching_link.has_permissions():
            if matching_link.has_user(user_id):
                return matching_link.get_access()
            else:
                return NO_ACCESS
        else:
            rel_path = RelativePath()
            rel_path.from_relative(matching_link.get_path())
            return self.get_permissions(user_id, rel_path)

    def get_path_from_link(self, link_str):
        matching_link = None
        for link in self._links:
            if link.id == link_str:
                matching_link = link
                break
        if matching_link is None:
            return None
        else:
            return matching_link.get_path()

    def has_link(self, link_id):
        # type: (str) -> bool
        for link in self._links:
            if link.id is link_id:
                return True
        return False

    def add_link(self, rel_path, link_str):
        # type: (RelativePath, str) -> Link
        link = Link(rel_path.to_string(), [], NO_ACCESS, link_str)
        self._links.append(link)
        return link

    def has_owner(self, user_id):
        owners_group = self.get_group(OWNERS_ID)
        if owners_group is not None:
            return owners_group.has_user(user_id)
        else:
            mylog('There is no owners group for this cloud. This is likely a programming error', '31')
        return False

    def add_owner(self, user_id):
        if not self.has_owner(user_id):
            owners_group = self.get_group(OWNERS_ID)
            if owners_group is not None:
                owners_group.add_user(user_id)
            else:
                mylog('There is no owners group for this cloud. This is likely a programming error', '31')

    def add_user_permission(self, new_user_id, rel_path, new_perms):
        # type: (int, RelativePath, int) -> None
        mylog('add_user_permission')
        mylog('{}'.format(self._files))
        rel_path_str = rel_path.to_string()
        if rel_path_str in self._files:
            file_perms = self._files[rel_path_str]
        else:
            # if file_perms is None:
            mylog('Making new FilePermissions object')
            file_perms = FilePermissions(rel_path_str)
        mylog(file_perms.__dict__)

        if new_user_id == PUBLIC_USER_ID:
            file_perms.add_group(PUBLIC_ID, new_perms)
        else:
            file_perms.add_user(new_user_id, new_perms)

        mylog(file_perms.__dict__)
        self._files[rel_path_str] = file_perms
        mylog('{}'.format(self._files))

    def _file_get_permissions(self, user_id, file_permissions):
        # type: (int, FilePermissions) -> int
        perms = NO_ACCESS
        for gid in file_permissions.get_group_ids():
            group = self.get_group(gid)
            if group is not None:
                if group.has_user(user_id):
                    group_perms = file_permissions.get_group_permissions(gid)
                    perms |= group_perms
                    if perms == RDWR_ACCESS:
                        return perms

        if user_id in file_permissions.get_user_ids():
            perms |= file_permissions.get_user_permissions(user_id)

        return perms

    @staticmethod
    def add_path(found_permissions, new_path, new_permissions):
        # type: ([{str: int}], str, int) -> [{str: int}]
        n = {'path': new_path, 'perms': new_permissions}
        found_permissions.append(n)
        return found_permissions

    def get_user_permissions(self, user_id):
        # type: (int) -> [{str: int}]
        """
        Retrieves all of the paths that the user can access and the access they
          have to each path.
        :param user_id:
        :return:
        """
        # todo:36
        # When we add a path, if there is a parent with greater permisions,
        #   we'll skip it (the file is already available via a parent)
        # if there's a parent, but the parent has less permissions, DON'T skip it.

        # first add all the paths that the public has access to
        # then, for each group the user is a part of,
        #   add each of the paths the group has access to.
        # then enumerate all the files the user has access to,
        #   and add them.

        # I guess the public group is a group after all, so we can just enumerate all groups
        found_permissions = []
        for path in self._files.keys():
            file_perms = self._files[path]
            perms = file_perms.get_user_permissions(user_id)
            if perms > NO_ACCESS:
                found_permissions = PrivateData.add_path(found_permissions, path, perms)
        return found_permissions

    def delete_paths(self, paths):
        # type: ([RelativePath]) -> bool
        """
        Removes a set of paths from the private data.
        Doesn't attempt to find any children of the paths passed in, so the
        caller should walk the directory tree first.
        """
        # TODO: What about children? We should probably be deleting all the children too
        # Unless of course the caller already put all the children in the argument
        result = False
        for path in paths:
            if path in self._files.keys():
                result = True
                self._files.pop(path)
        return result

    def commit(self):
        """
        Writes out the PrivateData to the .nebs backing.
        Similar to db.session.commit(), so that a series of changes chan be
        saved atomically, if any subset of those changes would be invalid.
        """
        # this probably will have more logic in the future.
        rd = self.write_backend(self.export_v0())
        return rd

    def read_json(self, json_string):
        rd = ResultAndData(False, None)
        try:
            json_obj = json.loads(json_string)
            if MAJ_VER_KEY not in json_string:
                raise ValueError

            maj_ver = json_obj[MAJ_VER_KEY]
            if maj_ver == 0:
                rd = self.read_v0(json_obj)
            else:
                message = 'Failed to decode .nebs data with invalid version ' \
                          '{}'.format(maj_ver)
                mylog(message, '31')
                rd = ResultAndData(False, message)

        except ValueError, e:
            mylog('ERROR: Failed to decode json data', '31')
            rd = ResultAndData(False, e)

        return rd

    def read_v0(self, json_obj):
        """
        Reads v0 json data into this structure.
        :return:
        """
        rd = ResultAndData(False, None)

        new_links = []
        for link in json_obj[LINKS_KEY]:
            new_link = Link(None, [], NO_ACCESS, '')
            new_link.from_serializable(link)
            new_links.append(new_link)
        self._links = new_links

        new_groups = []
        for group in json_obj[GROUPS_KEY]:
            new_group = Group(0, '', [])
            new_group.from_serializable(group)
            new_groups.append(new_group)
            if new_group.id > self._next_group_id:
                self._next_group_id = new_group.id + 1
        self._groups = new_groups

        new_files = {}
        for file in json_obj[FILES_KEY]:
            new_file = FilePermissions(None)
            new_file.from_serializable(file)
            new_files[new_file._filepath] = new_file
        self._files = new_files

        rd = ResultAndData(True, None)
        return rd

    def write_backend(self, data):
        rd = ResultAndData(False, None)
        try:
            path = self._file_location()
            out_file = open(path, mode='w')
            out_file.write(data)
            out_file.close()
            # mylog('Wrote backend for [{}]"{}"'.format(
            #     self._cloud.my_id_from_remote, self._cloud.name), '32')
            rd = ResultAndData(True, None)
        except IOError, e:
            rd = ResultAndData(False, str(e))
            mylog(str(e))
        return rd

    def read_backend(self):
        rd = ResultAndData(False, None)
        try:
            path = self._file_location()
            in_file = open(path, mode='r')
            data = in_file.read()
            rd = ResultAndData(True, data)
        except IOError, e:
            rd = ResultAndData(False, str(e))
        return rd

    def export_v0(self):
        obj = {
            MAJ_VER_KEY: self._version[0]
            , MIN_VER_KEY: self._version[1]
            , LINKS_KEY: [link.to_serializable() for link in self._links]
            , GROUPS_KEY: [group.to_serializable() for group in self._groups]
            , FILES_KEY: [file.to_serializable() for file in self._files.values()]
        }
        return json.dumps(obj, indent=2)

    def _file_location(self):
        cloud_root = self._cloud_root
        return os.path.join(cloud_root, '.nebs')

    def _file_exists(self):
        path = self._file_location()
        return os.path.exists(path)

    def get_next_group_id(self):
        id = self._next_group_id
        self._next_group_id += 1
        return id


