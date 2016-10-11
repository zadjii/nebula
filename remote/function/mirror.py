from common_util import send_error_and_close, mylog
from messages import GoRetrieveHereMessage, HostVerifyHostFailureMessage, \
    HostVerifyHostSuccessMessage, InvalidStateMessage, MirrorFailureMessage, \
    AuthErrorMessage
from msg_codes import send_generic_error_and_close
from remote import get_db, Host, Cloud, Session
from remote.models.HostHostFetchMapping import HostHostFetchMapping
from remote.util import get_cloud_by_name


def mirror_complete(connection, address, msg_obj):
    db = get_db()
    host_id = msg_obj.id
    cloudname = msg_obj.cname

    matching_host = db.session.query(Host).get(host_id)
    if matching_host is None:
        msg = 'There was no host with the ID[{}]'.format(host_id)
        resp = InvalidStateMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return

    matching_cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if matching_cloud is None:
        msg = 'No cloud with name {}'.format(cloudname)
        resp = InvalidStateMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return

    matching_cloud.hosts.append(matching_host)
    db.session.commit()
    mylog('Host[{}] finished mirroring cloud \'{}\''.format(host_id, cloudname))


def host_request_cloud(connection, address, msg_obj):
    db = get_db()
    host_id = msg_obj.id
    cloudname = msg_obj.cname
    username = msg_obj.uname
    password = msg_obj.passw

    # print('User provided {},{},{},{}'.format(
    #     host_id, cloudname, username, password
    # ))
    matching_host = db.session.query(Host).get(host_id)
    if matching_host is None:
        msg = 'There was no host with the ID[{}]'.format(host_id)
        resp = InvalidStateMessage(msg)
        connection.send_obj(resp)
        connection.close()
        return

    match = db.session.query(Cloud).filter_by(name=cloudname).first()
    if match is None:
        msg = 'No cloud with name {}'.format(cloudname)
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


def client_mirror(connection, address, msg_obj):
    db = get_db()
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

    match = db.session.query(Cloud).filter_by(name=cloudname).first()
    if match is None:
        msg = 'No cloud with name {}'.format(cloudname)
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
    # rand_host = match.hosts.first()
    rand_host = None
    if len(cloud.active_hosts()) > 0:
        rand_host = cloud.active_hosts()[0]  # todo make this random
    if rand_host is not None:
        # ip = rand_host.ip
        ip = rand_host.ipv6
        port = rand_host.port

        # Here we have to do what we did with HostClientVerify.
        # The remote now makes an entry saying that the requester is going to
        # rand_host. When the rand_host gets the HostHostFetch, then they'll ask
        # the remote if that host was told to fetch from rand_host.
        # we'll look up the entry, and return success/fail.
        #
        # HostHostFetch may in the future be also used for bulk syncing the
        # mirror. We'd have to make sure a similar entry exists in that
        # scenario.
        mapping = HostHostFetchMapping(rand_host, new_host, cloud)
        db.session.add(mapping)
        db.session.commit()
        mylog('Created a host mapping [{}]->[{}] for {}'.format(
            rand_host.id
            , new_host.id
            , (cloud.creator_name(), cloud.name)), '34;103')
        # see `host_verify_host`
    target_host_id = 0 if rand_host is None else rand_host.id
    owner_ids = [owner.id for owner in cloud.owners]
    # GoRetrieveHere kinda acts as the MirrorSuccess message I guess...
    msg = GoRetrieveHereMessage(target_host_id, ip, port, owner_ids)
    connection.send_obj(msg)

    print 'nebr has reached the end of host_request_cloud'


def host_verify_host(connection, address, msg_obj):
    db = get_db()
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





