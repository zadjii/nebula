from common_util import send_error_and_close, mylog, get_mylog
from messages import GoRetrieveHereMessage, HostVerifyHostFailureMessage, \
    HostVerifyHostSuccessMessage, InvalidStateMessage, MirrorFailureMessage, \
    AuthErrorMessage
from remote import Host, Cloud, Session
from remote.models.Mirror import Mirror
from remote.models.User import User
from remote.models.HostHostFetchMapping import HostHostFetchMapping
from remote.util import get_cloud_by_name, get_user_by_name


def mirror_complete(remote_obj, connection, address, msg_obj):
    db = remote_obj.get_db()
    host_id = msg_obj.id
    cloudname = msg_obj.cname

    matching_mirror = db.session.query(Mirror).get(host_id)
    if matching_mirror is None:
        msg = 'There was no mirror with the ID[{}]'.format(host_id)
        resp = InvalidStateMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return
    matching_mirror.completed_mirroring = True
    # matching_cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    # if matching_cloud is None:
    #     msg = 'No cloud with name {}'.format(cloudname)
    #     resp = InvalidStateMessage(msg)
    #     connection.send_obj(resp)
    #     connection.close()
    #     return
    # matching_cloud.hosts.append(matching_host)
    db.session.commit()
    mylog('Mirror[{}] finished mirroring cloud \'{}\''.format(host_id, cloudname))


def host_request_cloud(remote_obj, connection, address, msg_obj):
    db = remote_obj.get_db()
    _log = get_mylog()
    host_id = msg_obj.id
    cloud_uname = msg_obj.cloud_uname
    cloudname = msg_obj.cname
    username = msg_obj.username
    password = msg_obj.passw

    # print('User provided {},{},{},{}'.format(
    #     host_id, cloudname, username, password
    # ))
    matching_host = db.session.query(Host).get(host_id)
    if matching_host is None:
        msg = 'There was no host with the ID[{}]'.format(host_id)
        _log.debug(msg)
        resp = InvalidStateMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return

    creator = get_user_by_name(db, cloud_uname)
    if creator is None:
        msg = 'There was no cloud matching name {}/{}'.format(cloud_uname, cloudname)
        resp = InvalidStateMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return

    # match = db.session.query(Cloud).filter_by(name=cloudname).first()
    match = creator.created_clouds.filter_by(name=cloudname).first()
    if match is None:
        msg = 'No cloud with name {}/{}'.format(cloud_uname, cloudname)
        resp = MirrorFailureMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return

    # user = db.session.query(User).filter_by(username=username).first()
    user = match.owners.filter_by(username=username).first()
    if user is None:
        msg = '{} is not an owner of {}'.format(user.username, cloudname)
        resp = MirrorFailureMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return
    verify_password = user.check_password(password)
    if not verify_password:
        msg = 'Invalid username/password'
        resp = AuthErrorMessage()
        connection.send_obj(resp)
        connection.close()
        return

    respond_to_mirror_request(db, connection, address, matching_host, match)


def client_mirror(remote_obj, connection, address, msg_obj):
    db = remote_obj.get_db()
    session_id = msg_obj.sid
    host_id = msg_obj.host_id
    cloud_uname = msg_obj.cloud_uname
    # the cloud uname is currently unused, it will eventually be used
    cloudname = msg_obj.cname

    matching_host = db.session.query(Host).get(host_id)
    if matching_host is None:
        msg = 'There was no host with the ID[{}]'.format(host_id)
        resp = InvalidStateMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return

    # todo: It'll be easier on the DB to find the user first, then filter their
    #   owned clouds to find the match

    creator = get_user_by_name(db, cloud_uname)
    if creator is None:
        msg = 'There was no cloud matching name {}/{}'.format(cloud_uname, cloudname)
        resp = InvalidStateMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return

    # match = db.session.query(Cloud).filter_by(name=cloudname).first()
    match = creator.created_clouds.filter_by(name=cloudname).first()
    if match is None:
        msg = 'No cloud with name {}/{}'.format(cloud_uname, cloudname)
        resp = MirrorFailureMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return

    session = db.session.query(Session).filter_by(uuid=session_id).first()
    if session is None:
        msg = 'provided session ID does not exist'
        resp = InvalidStateMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return

    user = session.user
    cloud_user = match.owners.filter_by(username=user.username).first()
    if cloud_user is None:
        # send_generic_error_and_close(connection)
        # print [owner.username for owner in match.owners.all()]
        # raise Exception(user.name + ' is not an owner of ' + cloudname)
        msg = '{} is not an owner of {}'.format(user.username, cloudname)
        resp = MirrorFailureMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return
    # user is an owner, and the host exists
    respond_to_mirror_request(db, connection, address, matching_host, match)


def respond_to_mirror_request(db, connection, address, new_host, cloud):
    """Assumes that the requester has already been validated"""
    ip = '0'
    port = 0

    new_mirror = Mirror()
    db.session.add(new_mirror)
    cloud.mirrors.append(new_mirror)
    new_host.mirrors.append(new_mirror)
    db.session.commit()

    # rand_host = match.hosts.first()
    # FIXME why is this rand_mirror then rand_host???????
    rand_mirror = None
    if len(cloud.active_hosts()) > 0:
        rand_mirror = cloud.active_hosts()[0]  # todo make this random
    if rand_mirror is not None:
        # ip = rand_host.ip
        ip = rand_mirror.host.ip()
        port = rand_mirror.host.port

        # Here we have to do what we did with HostClientVerify.
        # The remote now makes an entry s
        # aying that the requester is going to
        # rand_host. When the rand_host gets the HostHostFetch, then they'll ask
        # the remote if that host was told to fetch from rand_host.
        # we'll look up the entry, and return success/fail.
        #
        # HostHostFetch may in the future be also used for bulk syncing the
        # mirror. We'd have to make sure a similar entry exists in that
        # scenario.
        mapping = HostHostFetchMapping(rand_mirror, new_mirror, cloud)
        db.session.add(mapping)
        db.session.commit()
        mylog('Created a host mapping [{}]->[{}] for {}'.format(
            rand_mirror.id
            , new_host.id
            , (cloud.uname(), cloud.cname())), '34;103')
        # see `host_verify_host`
    target_host_id = 0 if rand_mirror is None else rand_mirror.id
    owner_ids = [owner.id for owner in cloud.owners]
    # GoRetrieveHere kinda acts as the MirrorSuccess message I guess...
    msg = GoRetrieveHereMessage(new_mirror.id, target_host_id, ip, port, owner_ids, cloud.max_size)
    connection.send_obj(msg)

    mylog('nebr has reached the end of host_request_cloud')


def host_verify_host(remote_obj, connection, address, msg_obj):
    db = remote_obj.get_db()
    # the receiver recieved the HHF message, the sender sent it.
    # the receiver is the old mirror, the sender is the new mirror
    reciever_id = msg_obj.my_id
    sender_id = msg_obj.their_id
    cloud_uname = msg_obj.cloud_uname
    cloudname = msg_obj.cname
    cloud = get_cloud_by_name(db, cloud_uname, cloudname)
    if cloud is None:
        msg = 'No matching cloud {}'.format((cloud_uname, cloudname))
        err = HostVerifyHostFailureMessage(msg)
        send_error_and_close(err, connection)
        return

    mappings = db.session.query(HostHostFetchMapping)
    # mylog('mappings 1 = {}'.format([(mapping.old_host_id, mapping.new_host_id)
    #                                 for mapping in mappings.all()]))
    mappings = mappings.filter_by(
        old_host_id=reciever_id
        , new_host_id=sender_id
        , cloud_id=cloud.id)

    # mylog('mappings 2 = {}'.format([(mapping.old_host_id, mapping.new_host_id)
    #                                 for mapping in mappings.all()]))

    # mylog('Number of mappings={}'.format(mappings.count()))
    found_mapping = None

    for mapping in mappings.all():
        if mapping.has_timed_out():
            # mylog('a mapping timed out, deleting')
            db.session.delete(mapping)
        elif found_mapping is None:
            found_mapping = mapping
            # mylog('found matching mapping')
        else:  # a valid mapping that's a duplicate
            # mylog('duplicate mapping, deleting')
            db.session.delete(mapping)
    db.session.commit()
    if found_mapping is not None:
        msg = HostVerifyHostSuccessMessage(reciever_id, sender_id, cloud_uname, cloudname)
        connection.send_obj(msg)
    else:
        msg = 'No matching host mapping [{}]->[{}] for {}'.format(
            reciever_id
            , sender_id
            , (cloud_uname, cloudname))
        mylog('ERR:{}, {}'.format(msg, mappings.all()))
        err = HostVerifyHostFailureMessage(msg)
        send_error_and_close(err, connection)
        return





