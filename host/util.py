import socket
import ssl
import os
from netifaces import interfaces, ifaddresses, AF_INET6
# from host import Cloud
from OpenSSL import crypto

from common.SimpleDB import SimpleDB
from host.models import FileNode
from host.models.Client import Client
from host.models.Cloud import Cloud
from messages import HostVerifyClientRequestMessage
from msg_codes import HOST_VERIFY_CLIENT_SUCCESS
from common_util import *

FILE_SYNC_PROPOSAL_ACKNOWLEDGE = 0
FILE_SYNC_PROPOSAL_REJECT = 1
FILE_SYNC_PROPOSAL_ACCEPT = 2

FILE_CHANGE_TYPE_CREATE = 0
FILE_CHANGE_TYPE_MODIFY = 1
FILE_CHANGE_TYPE_DELETE = 2
FILE_CHANGE_TYPE_MOVE = 3


def get_matching_clouds(db, mirror_id):
    # type: (SimpleDB, int) -> ResultAndData
    # type: (SimpleDB, int) -> ResultAndData(True, Cloud)
    # type: (SimpleDB, int) -> ResultAndData(False, str)
    rd = Error()
    matching_id_clouds = db.session.query(Cloud)\
        .filter(Cloud.my_id_from_remote == mirror_id)

    if matching_id_clouds.count() <= 0:
        rd = Error('Received a message intended for id={},'
                   ' but I don\'t have any clouds with that id'
                   .format(mirror_id))
    elif matching_id_clouds.count() > 1:
        rd = Error('Found more than one mirror for id_from_remote={}'.format(mirror_id))
    else:
        rd = ResultAndData(True, matching_id_clouds.first())
    return rd


def all_ip6_list():
    ip_list = []
    for interface in interfaces():
        for link in ifaddresses(interface)[AF_INET6]:
            ip_list.append(link['addr'])
    # add ::1 to the end of the list so if we're in debug mode,
    #  its only a last resort.
    if '::1' in ip_list:
        ip_list.remove('::1')
        ip_list.append('::1')
    return ip_list


def get_ipv6_list():
    """Returns all suitable (public) ipv6 addresses for this host"""
    valid_ips = [ip for ip in all_ip6_list() if ('%' not in ip)]
    # todo: remove this from the Release build  of nebula, so the conditional
    #   is never even checked.
    if os.environ.get('NEBULA_LOCAL_DEBUG', False):
        return valid_ips
    else:
        return [ip for ip in valid_ips if (not ip == '::1')]


def check_response(expected, recieved):
    if not(int(expected) == int(recieved)):
        raise Exception('Received wrong msg-code, '
                        'expected {}, recieved {}'.format(expected, recieved))


def get_clouds_by_name(db, uname, cname):
    # type: (SimpleDB, str, str) -> [Cloud]
    # return [cloud for cloud in db.session.query(Cloud).filter_by(name=cname)]
    # return [cloud for cloud in db.session.query(Cloud).filter_by(username=uname, name=cname)]
    # return db.session.query(Cloud).filter_by(username=uname, name=cname).all()
    return db.session.query(Cloud).filter(Cloud.username.ilike(uname)).filter_by(name=cname).all()


def get_client_session(db, uuid, cloud_uname, cloud_cname):
    if uuid is None:
        return Success(None)
    rd = Error()
    matching_clients = db.session.query(Client).filter_by(uuid=uuid).all()
    if len(matching_clients) < 1:
        rd = Error('No matching session')
    else:
        for client in matching_clients:
            if client.has_timed_out():
                mylog('client has timed out.')
                db.session.delete(client)
                db.session.commit()
                continue
            if client.cloud.uname() == cloud_uname and client.cloud.cname() == cloud_cname:
                rd = ResultAndData(True, client)
                break
        if not rd.success:
            rd = Error('No matching session')
    return rd


def validate_or_get_client_session(db, uuid, cloud_uname, cloud_cname):
    rd = get_client_session(db, uuid, cloud_uname, cloud_cname)
    mylog('validate_or_get_client_session[{}]={}'.format(0, rd))
    if rd.success:
        client = rd.data
        if client is not None:
            client.refresh()
        db.session.commit()
        mylog('Found a valid session for this request')
        # great, this client is good to go
        pass
    else:
        clouds = get_clouds_by_name(db, cloud_uname, cloud_cname)
        # okay, so weirdness. Technically, nebs is going to be asking each
        # remote if any of these clouds were the right one.
        # and technically, there could be two different remotes with the same
        # un/cn pair on them. So one of them could be true, the other not.
        # they could both be true. one could even fake that it's true to spoof
        # the real one.
        # obviously, #fixme #todo:16
        verified_cloud = False
        for cloud in clouds:
            # for each cloud, connect to it, ask about the client.
            # if the client is alright, make an entry for it and return it.
            # otherwise, keep looking.
            rd = cloud.get_remote_conn()
            mylog('acquired a connection to the remote')
            if rd.success:
                conn = rd.data
                msg = HostVerifyClientRequestMessage(cloud.my_id_from_remote
                                                     , uuid
                                                     , cloud_uname
                                                     , cloud_cname)
                conn.send_obj(msg)
                response = conn.recv_obj()
                if response.type == HOST_VERIFY_CLIENT_SUCCESS:
                    # client = Client(uuid, response.user_id)
                    client = Client()
                    client.uuid = uuid
                    client.user_id = response.user_id
                    db.session.add(client)
                    cloud.clients.append(client)
                    db.session.commit()
                    rd = ResultAndData(True, client)
                    mylog('Successfully verified the client with the remote')
                    # mylog('client.cloud={}'.format(client.cloud.full_name()))
                    verified_cloud = True
                    break
                else:
                    continue
        if not verified_cloud:
            rd = Error()
            mylog('validate_or_get_client_session[{}]={}'.format(4, rd))
    if not rd.success:
        rd = ResultAndData(False,
                           'Could not verify client session={}'.format(uuid))
        mylog(rd.data)
    return rd


def setup_ssl_socket_for_address(addr, port):
    # type: (str, int) -> ResultAndData
    _log = get_mylog()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((addr, port))
    except Exception, e:
        err = 'Generic error establising connection to {},{}:{}'.format(addr, port, e.message)
        _log.error(err)
        return Error(err)

    try:
        sslSocket = ssl.wrap_socket(s)
        return Success(sslSocket)
    except Exception, e:
        err = 'Error initiating SSL when establising connection to {}:{}, {}'.format(addr, port, e.__dict__)
        _log.error(err)
        return Error(err)


def setup_remote_socket(cloud):
    # type: (Cloud) -> ResultAndData
    _log = get_mylog()
    remote = cloud.remote
    if remote is not None:
        return remote.setup_socket()
    err = 'Cloud [] does not have a Remote associated with it. That shouldn\'t be possible.'
    _log.error(err)
    return Error(err)


def permissions_are_sufficient(permissions, requested):
    return (permissions & requested) == requested


def get_breadth_first_children(root):
    # type: (FileNode) -> [(str, FileNode)]
    children = [('.', root)]
    num_children = 1
    i = 0
    while i < num_children:
        parent = children[i][1]
        parent_full_path = children[i][0]
        new_children = parent.children
        for child in new_children.all():
            children.append((os.path.join(parent_full_path, child.name), child))
        i += 1
        num_children += new_children.count()
    children.pop(0)  # remove the root
    return children


def remove_all_parents(children, index):
    # type: ([(str, FileNode)], int) -> [(str, FileNode)]
    """
    Children must be a reverse BFS of nodes for this to work.
    :param children:
    :param index:
    :return:
    """
    child_path, child = children[index]
    path_elems = os.path.normpath(child_path).split(os.path.sep)
    subset = children[index:]
    last_parent_index = index
    for i in range(0, len(path_elems)):
        elem = path_elems[i]
        found_parent = False
        for j in range(last_parent_index, len(children)):
            family_path, family_node = children[j]
            if family_node.name == elem:
                last_parent_index = j
                children.pop(last_parent_index)
                found_parent = True
                break
        # If the parent wasn't found, then the parent isn't a Node at all
        # That means we've iterated on all parents in this list
        # OR the parent was already taken out of this list. Which is good enough.
        if not found_parent:
            break

    return children


def find_deletable_children(root, full_path, timestamp):
    # type: (FileNode, str, datetime) -> [(str, FileNode)]
    # find all children of this node, BFS
    # reverse the order (bottom up)
    # for node in children:
    #   if node.mtime < timestamp
    #       remove all of it's parents from the list
    #       remove it from the list
    #   else
    #       leave in the list
    # remove all nodes still in the list
    children = get_breadth_first_children(root)
    children = children[::-1]  # my favorite python operator
    deleteables = []
    i = 0
    done = i >= len(children)
    while not done:
        # mylog('find_deletable_children {}/{}'.format(i, len(children)))
        # print('find_deletable_children {}/{}'.format(i, len(children)))
        child_path, node = children[i]
        child_mtime = node.last_modified
        if child_mtime > timestamp:
            children = remove_all_parents(children, i)
            children.pop(i)
            # leave i where it is, the next node is at that index now.
        else:
            i += 1
        done = i >= len(children)

    return children


def lookup_remote(db, remote_address, remote_port):
    # type: (SimpleDB, str, int) -> ResultAndData
    # type: (SimpleDB, str, int) -> ResultAndData(True, Optional[Remote])
    # type: (SimpleDB, str, int) -> ResultAndData(False, str)
    _log = get_mylog()
    rd = Error()
    from host.models.Remote import Remote
    remotes = db.session.query(Remote)

    _log.debug('All remotes:')
    for remote in remotes.all():
        _log.debug(remote.debug_str())

    remotes = remotes.filter_by(remote_address=remote_address, remote_port=remote_port)
    _log.debug('Matching remotes:')
    for remote in remotes.all():
        _log.debug(remote.debug_str())

    if remotes.count() > 1:
        msg = 'Found more than one remote entry matching {}:{}'.format(remote_address, remote_port)
        rd = Error(msg)
    elif remotes.count() == 0:
        rd = Success(None)
    else:
        remote = remotes.first()
        rd = Success(remote)
    return rd


def create_key_pair(type, bits):
    # type: (int, int) -> crypto.PKey
    """
    Create a public/private key pair.
    Arguments: type - Key type, must be one of TYPE_RSA and TYPE_DSA
               bits - Number of bits to use in the key
    Returns:   The public/private key pair in a PKey object
    """
    pkey = crypto.PKey()
    pkey.generate_key(type, bits)
    return pkey


def create_cert_request(pkey, digest="sha256", **name):
    # type: (crypto.PKey, str, dict) -> crypto.X509Req
    """
    Create a certificate request.
    Arguments: pkey   - The key to associate with the request
               digest - Digestion method to use for signing, default is md5
               **name - The name of the subject of the request, possible
                        arguments are:
                          C     - Country name
                          ST    - State or province name
                          L     - Locality name
                          O     - Organization name
                          OU    - Organizational unit name
                          CN    - Common name
                          emailAddress - E-mail address
    Returns:   The certificate request in an X509Req object
    """
    req = crypto.X509Req()
    subj = req.get_subject()

    for (key, value) in name.items():
        setattr(subj, key, value)

    req.set_pubkey(pkey)
    req.sign(pkey, digest)
    return req
